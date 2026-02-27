"""
Email processing routes
"""
from fastapi import APIRouter, Depends, HTTPException, status, Query
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, desc
from database import get_db
from models.admin import Admin
from schemas.email import EmailProcessRequest, EmailResponse
from services.tenant import tenant_service
from services.policy_loader import policy_loader_service
from services.audit_logger import audit_logger_service
from services.flow1 import Flow1Orchestrator
from models.email import Email
from models.draft import Draft
from models.company import Company
import uuid
import logging
from datetime import datetime
from typing import Optional
from auth.jwt import get_current_admin

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/api/emails", tags=["Emails"])


@router.post("/process", response_model=dict)
async def process_email(
    email_request: EmailProcessRequest,
    db: AsyncSession = Depends(get_db)
):
    """
    Process incoming email (called by n8n)
    This endpoint:
    1. Maps credential_id to company_id
    2. Checks for duplicate emails (gmail_message_id)
    3. Creates email record
    4. Runs classification agents (Phase 2+)
    5. Creates draft if needed (Phase 5+)
    """
    email_data = email_request.email_data
    
    # Validate required fields
    if not email_data.get("subject") and not email_data.get("body"):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Email must have at least subject or body"
        )
    
    # Map credential_id to company_id
    company_id = await tenant_service.map_credential_to_company(
        db, email_request.credential_id
    )
    
    if not company_id:
        # Try mapping by email
        to_email = email_data.get("to", "")
        company = await tenant_service.get_company_by_email(db, to_email)
        if not company:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Company not found for credential_id: {email_request.credential_id}"
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
    subject = email_data.get("subject", "")
    body = email_data.get("body", "")
    from_email = email_data.get("from", "")
    to_email = email_data.get("to", "")
    thread_id = email_data.get("thread_id")
    
    # Process email through Flow 1 LangGraph workflow
    orchestrator = Flow1Orchestrator()
    
    try:
        result = await orchestrator.process_email(
            db=db,
            company_id=company_id,
            email_data={
                "subject": subject,
                "body": body,
                "from": from_email,
                "to": to_email,
                "thread_id": thread_id,
                "gmail_message_id": gmail_message_id
            }
        )
        
        # Log email processing (non-blocking - don't fail if logging fails)
        try:
            await audit_logger_service.log_email_processed(
                db=db,
                company_id=company_id,
                email_id=result["email_id"],
                classification_metadata=result.get("classification", {})
            )
        except Exception as e:
            import logging
            logger = logging.getLogger(__name__)
            logger.warning(f"Error logging email processing: {str(e)}")
        
        # Handle duplicate_skipped status gracefully
        if result.get("status") == "duplicate_skipped":
            return {
                "email_id": result.get("email_id"),
                "draft_id": result.get("draft_id"),
                "status": "duplicate",
                "message": result.get("message", "Email was already processed")
            }
        
        email_id_str = result.get("email_id")
        if email_id_str:
            try:
                from services.lead_replied_crm import record_lead_replied_if_applicable
                await record_lead_replied_if_applicable(db, email_id_str)
            except Exception as e:
                logger.warning("Could not record lead replied in CRM: %s", e)
        
        return {
            "email_id": result["email_id"],
            "draft_id": result.get("draft_id"),
            "company_id": company_id,
            "status": result.get("status", "processed"),
            "classification": result.get("classification", {}),
            "executive_summary": result.get("executive_summary"),
            "recommended_action": result.get("recommended_action"),
            "message": "Email processed successfully"
        }
        
    except Exception as e:
        import logging
        logger = logging.getLogger(__name__)
        logger.error(f"Error processing email through Flow 1: {str(e)}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error processing email: {str(e)}"
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

