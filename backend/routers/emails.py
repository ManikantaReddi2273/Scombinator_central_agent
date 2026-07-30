"""
Email processing routes
"""
from fastapi import APIRouter, Depends, HTTPException, status, Query, BackgroundTasks
from fastapi.responses import JSONResponse
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, desc
from database import get_db, AsyncSessionLocal
from models.admin import Admin
from schemas.email import EmailProcessRequest, EmailResponse
from services.tenant import tenant_service
from services.audit_logger import audit_logger_service
from services.flow1 import Flow1Orchestrator
from models.email import Email
from models.company import Company
import uuid
import asyncio
import logging
from typing import Optional, Dict, Any
from auth.jwt import get_current_admin

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/api/emails", tags=["Emails"])

# One Flow 1 at a time — parallel OpenAI + LangGraph OOMs / 502s Render free tier
_flow1_semaphore = asyncio.Semaphore(1)


async def _process_email_background(
    company_id: str,
    email_payload: Dict[str, Any],
    email_id: Optional[str] = None,
) -> None:
    """
    Run Flow 1 in a fresh DB session after the HTTP response is sent.
    Serialized so free-tier Render does not crash under concurrent AI jobs.
    """
    async with _flow1_semaphore:
        async with AsyncSessionLocal() as db:
            try:
                if email_id:
                    email_payload = {**email_payload, "email_id": email_id}

                orchestrator = Flow1Orchestrator()
                result = await orchestrator.process_email(
                    db=db,
                    company_id=company_id,
                    email_data=email_payload,
                )
                try:
                    await audit_logger_service.log_email_processed(
                        db=db,
                        company_id=company_id,
                        email_id=result.get("email_id"),
                        classification_metadata=result.get("classification", {}),
                    )
                except Exception as e:
                    logger.warning("Background audit log failed: %s", e)

                email_id_str = result.get("email_id")
                if email_id_str:
                    try:
                        from services.lead_replied_crm import record_lead_replied_if_applicable
                        await record_lead_replied_if_applicable(db, email_id_str)
                    except Exception as e:
                        logger.warning("Could not record lead replied in CRM: %s", e)

                await db.commit()
                logger.info(
                    "Background Flow 1 finished company=%s email_id=%s draft_id=%s status=%s",
                    company_id,
                    result.get("email_id"),
                    result.get("draft_id"),
                    result.get("status"),
                )
            except Exception as e:
                await db.rollback()
                logger.error(
                    "Background Flow 1 failed for company %s email_id=%s: %s",
                    company_id,
                    email_id,
                    e,
                    exc_info=True,
                )


@router.post("/process", response_model=dict)
async def process_email(
    email_request: EmailProcessRequest,
    background_tasks: BackgroundTasks,
    db: AsyncSession = Depends(get_db),
):
    """
    Accept an inbound email from n8n and process it with Flow 1.

    Persists a queued email row immediately, returns HTTP 202, then runs AI
    in a single-file background queue (avoids Render free-tier 502/OOM).
    """
    email_data = email_request.email_data
    
    # Validate required fields
    if not email_data.get("subject") and not email_data.get("body"):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Email must have at least subject or body"
        )
    
    # Map company: prefer company_id (Render OAuth), then n8n credential_id, then to-email
    company_id = None
    if email_request.company_id:
        company = await tenant_service.get_company_by_id(db, email_request.company_id)
        if company:
            company_id = str(company.company_id)
        else:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Company not found for company_id: {email_request.company_id}"
            )
    elif email_request.credential_id:
        company_id = await tenant_service.map_credential_to_company(
            db, email_request.credential_id
        )
        # credential_id might actually be a company UUID (Render OAuth path)
        if not company_id:
            company = await tenant_service.get_company_by_id(db, email_request.credential_id)
            if company:
                company_id = str(company.company_id)

    if not company_id:
        # Try mapping by email
        to_email = email_data.get("to", "")
        company = await tenant_service.get_company_by_email(db, to_email)
        if not company:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=(
                    f"Company not found for credential_id={email_request.credential_id!r}, "
                    f"company_id={email_request.company_id!r}, to={to_email!r}"
                )
            )
        company_id = str(company.company_id)
    
    # Duplicate Prevention: Check if gmail_message_id already exists
    gmail_message_id = email_data.get("gmail_message_id")
    if gmail_message_id:
        existing_result = await db.execute(
            select(Email).where(Email.gmail_message_id == gmail_message_id)
        )
        existing = existing_result.scalar_one_or_none()
        if existing:
            # Email already processed, return existing record
            return {
                "email_id": str(existing.id),
                "company_id": company_id,
                "status": "duplicate",
                "message": "Email already processed"
            }
    
    # Extract email data
    subject = email_data.get("subject", "") or "(No Subject)"
    body = email_data.get("body", "") or ""
    from_email = email_data.get("from", "") or "unknown@unknown"
    to_email = email_data.get("to", "") or ""
    thread_id = email_data.get("thread_id")

    # Persist stub immediately so every accepted email is visible and Flow 1 can update it
    queued = Email(
        id=uuid.uuid4(),
        company_id=uuid.UUID(company_id),
        subject=subject[:500],
        body=body,
        from_email=from_email[:255],
        to_email=to_email[:255] if to_email else "unknown@unknown",
        thread_id=thread_id,
        gmail_message_id=gmail_message_id,
        function="Admin",
        intent="Inquiry",
        urgency="Can wait",
        impact="Low",
        confidence="Missing info",
        priority_score="0",
        executive_summary="Queued for AI processing",
        recommended_action=None,
        classification_metadata={"status": "queued"},
        email_type="inbound",
    )
    try:
        db.add(queued)
        await db.flush()
        await db.refresh(queued)
        queued_email_id = str(queued.id)
        # Commit before background task so the stub row is visible to Flow 1
        await db.commit()
    except Exception as e:
        await db.rollback()
        # Race: another worker inserted the same gmail_message_id
        if gmail_message_id:
            existing_result = await db.execute(
                select(Email).where(Email.gmail_message_id == gmail_message_id)
            )
            existing = existing_result.scalar_one_or_none()
            if existing:
                return {
                    "email_id": str(existing.id),
                    "company_id": company_id,
                    "status": "duplicate",
                    "message": "Email already processed",
                }
        logger.error("Failed to queue email stub: %s", e, exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to queue email: {e}",
        )

    email_payload = {
        "subject": subject,
        "body": body,
        "from": from_email,
        "to": to_email,
        "thread_id": thread_id,
        "gmail_message_id": gmail_message_id,
        "email_id": queued_email_id,
    }

    # Queue AI pipeline after response — prevents Render free-tier gateway timeouts
    background_tasks.add_task(
        _process_email_background,
        company_id,
        email_payload,
        queued_email_id,
    )

    return JSONResponse(
        status_code=status.HTTP_202_ACCEPTED,
        content={
            "email_id": queued_email_id,
            "company_id": company_id,
            "status": "accepted",
            "gmail_message_id": gmail_message_id,
            "message": (
                "Email accepted for AI processing. "
                "Classification and draft will appear in the dashboard shortly."
            ),
        },
    )


@router.get("/priority-queue", response_model=list[dict])
async def get_priority_queue(
    limit: int = Query(20, ge=1, le=100, description="Number of results"),
    db: AsyncSession = Depends(get_db),
    admin: Admin = Depends(get_current_admin)
):
    """
    Get unified priority queue across all companies
    Returns emails sorted by priority score with company context
    """
    from sqlalchemy import cast, Integer
    query = select(Email, Company.name, Company.email).join(
        Company, Email.company_id == Company.company_id
    ).order_by(
        desc(cast(Email.priority_score, Integer)),
        desc(Email.created_at)
    ).limit(limit)
    
    result = await db.execute(query)
    rows = result.all()
    
    queue = []
    for email, company_name, company_email in rows:
        queue.append({
            "email_id": str(email.id),
            "company_id": str(email.company_id),
            "company_name": company_name,
            "company_email": company_email,
            "subject": email.subject,
            "from_email": email.from_email,
            "to_email": email.to_email,
            "email_type": email.email_type,
            "priority_score": email.priority_score,
            "function": email.function,
            "intent": email.intent,
            "executive_summary": email.executive_summary,
            "recommended_action": email.recommended_action,
            "created_at": email.created_at.isoformat()
        })
    
    return queue


@router.get("/", response_model=list[EmailResponse])
async def list_emails(
    company_id: Optional[str] = Query(None, description="Filter by company ID"),
    function: Optional[str] = Query(None, description="Filter by function (Sales/Hiring/Legal/etc)"),
    status: Optional[str] = Query(None, description="Filter by status"),
    priority_min: Optional[int] = Query(None, description="Minimum priority score"),
    limit: int = Query(50, ge=1, le=100, description="Number of results"),
    db: AsyncSession = Depends(get_db),
    admin: Admin = Depends(get_current_admin)
):
    """
    List emails with filters (admin only)
    Supports filtering by company, function, priority score
    """
    query = select(Email)
    
    if company_id:
        query = query.where(Email.company_id == uuid.UUID(company_id))
    if function:
        query = query.where(Email.function == function)
    if priority_min:
        # Filter by priority score (stored as string, convert for comparison)
        from sqlalchemy import cast, Integer
        query = query.where(
            cast(Email.priority_score, Integer) >= priority_min
        )
    
    # Order by priority score (descending) and created_at
    from sqlalchemy import cast, Integer
    query = query.order_by(
        desc(cast(Email.priority_score, Integer)),
        desc(Email.created_at)
    ).limit(limit)
    
    result = await db.execute(query)
    emails = result.scalars().all()
    
    return [
        EmailResponse(
            id=e.id,
            company_id=e.company_id,
            subject=e.subject,
            from_email=e.from_email,
            to_email=e.to_email,
            thread_id=e.thread_id,
            thread_history=[],
            thread_count=0,
            email_type=e.email_type,
            function=e.function,
            intent=e.intent,
            priority_score=e.priority_score,
            executive_summary=e.executive_summary,
            recommended_action=e.recommended_action,
            created_at=e.created_at
        )
        for e in emails
    ]


@router.get("/{email_id}", response_model=EmailResponse)
async def get_email(
    email_id: str,
    db: AsyncSession = Depends(get_db)
):
    """
    Get email by ID with full details including thread history
    No auth required - n8n calls this directly, but admin can also use it
    """
    result = await db.execute(
        select(Email).where(Email.id == uuid.UUID(email_id))
    )
    email = result.scalar_one_or_none()
    
    if not email:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Email not found"
        )
    
    # Load thread history if thread_id exists
    thread_history = []
    thread_count = 0
    if email.thread_id:
        try:
            orchestrator = Flow1Orchestrator()
            thread_history = await orchestrator._load_thread_history(
                db=db,
                company_id=str(email.company_id),
                thread_id=email.thread_id,
                current_gmail_message_id=email.gmail_message_id
            )
            thread_count = len(thread_history)
        except Exception as e:
            logger.warning(f"Error loading thread history for email {email_id}: {str(e)}")
            # Continue with empty history
    
    # Parse recipient_context for outbound/reply-in-thread (n8n uses it for update-crm lead_id)
    recipient_context = None
    if email.recipient_context:
        try:
            import json
            if isinstance(email.recipient_context, dict):
                recipient_context = email.recipient_context
            else:
                recipient_context = json.loads(email.recipient_context)
        except Exception:
            pass
    
    return EmailResponse(
        id=email.id,
        company_id=email.company_id,
        subject=email.subject,
        from_email=email.from_email,
        to_email=email.to_email,
        thread_id=email.thread_id,
        gmail_message_id=email.gmail_message_id,  # Include for threading
        thread_history=thread_history,
        thread_count=thread_count,
        email_type=email.email_type,  # Include email_type for n8n workflow
        recipient_context=recipient_context,
        function=email.function,
        intent=email.intent,
        priority_score=email.priority_score,
        executive_summary=email.executive_summary,
        recommended_action=email.recommended_action,
        created_at=email.created_at
    )
