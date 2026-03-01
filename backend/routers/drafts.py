"""
Draft management routes
"""
import logging
from fastapi import APIRouter, Depends, HTTPException, status, Query
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, desc
from database import get_db
from models.admin import Admin
from models.draft import Draft
from models.email import Email
from schemas.draft import (
    DraftResponse,
    DraftStatusResponse,
    DraftApproveRequest,
    DraftSentRequest,
    DraftAIEditRequest,
    DraftAIEditResponse,
)
from services.draft_ai_edit import edit_draft_with_ai
from services.audit_logger import audit_logger_service
from auth.jwt import get_current_admin
from datetime import datetime
from typing import Optional
import uuid

logger = logging.getLogger(__name__)
router = APIRouter(prefix="/api/drafts", tags=["Drafts"])


@router.get("/approved", response_model=list[DraftResponse])
async def get_approved_drafts(
    limit: int = Query(10, ge=1, le=100, description="Number of results"),
    db: AsyncSession = Depends(get_db)
):
    """
    Get approved drafts ready to send (called by n8n)
    No admin auth required - n8n calls this directly
    """
    query = select(Draft).where(Draft.status == "approved")
    query = query.order_by(desc(Draft.created_at)).limit(limit)
    
    result = await db.execute(query)
    drafts = result.scalars().all()
    
    return [
        DraftResponse(
            id=d.id,
            company_id=d.company_id,
            email_id=d.email_id,
            subject=d.subject,
            body=d.body,
            status=d.status,
            version=d.version,
            template_used=d.template_used,
            created_at=d.created_at
        )
        for d in drafts
    ]


@router.get("/pending", response_model=list[dict])
async def get_pending_drafts(
    company_id: Optional[str] = Query(None, description="Filter by company ID"),
    limit: int = Query(20, ge=1, le=100, description="Number of results"),
    db: AsyncSession = Depends(get_db),
    admin: Admin = Depends(get_current_admin)
):
    """
    Get pending drafts awaiting approval (admin only)
    This is the main queue for admin review
    Returns drafts with email and company information
    """
    from uuid import UUID
    from models.email import Email
    from models.company import Company
    
    query = (
        select(Draft, Email, Company)
        .join(Email, Draft.email_id == Email.id, isouter=True)
        .join(Company, Draft.company_id == Company.company_id)
        .where(Draft.status == "pending")
    )
    
    if company_id:
        try:
            query = query.where(Draft.company_id == UUID(company_id))
        except ValueError:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Invalid company_id format"
            )
    
    query = query.order_by(desc(Draft.created_at)).limit(limit)
    
    result = await db.execute(query)
    rows = result.all()
    
    drafts_with_context = []
    for draft, email, company in rows:
        draft_dict = {
            "id": str(draft.id),
            "company_id": str(draft.company_id),
            "email_id": str(draft.email_id) if draft.email_id else None,
            "subject": draft.subject,
            "body": draft.body,
            "status": draft.status,
            "version": draft.version,
            "template_used": draft.template_used,
            "created_at": draft.created_at,
            "company_name": company.name if company else None,
            "company_email": company.email if company else None,
        }
        
        # Add email context if available (include trigger_type, recipient_context for follow-up UI)
        if email:
            rc = email.recipient_context
            if hasattr(rc, "__iter__") and not isinstance(rc, (str, bytes)):
                pass  # keep as dict
            elif isinstance(rc, str):
                try:
                    import json
                    rc = json.loads(rc) if rc else None
                except Exception:
                    rc = None
            draft_dict["email"] = {
                "id": str(email.id),
                "subject": email.subject,
                "from_email": email.from_email,
                "to_email": email.to_email,
                "email_type": email.email_type,
                "trigger_type": getattr(email, "trigger_type", None),
                "recipient_context": rc,
                "body": email.body,
                "priority_score": email.priority_score,
                "executive_summary": email.executive_summary,
                "function": email.function,
                "intent": email.intent,
                "urgency": email.urgency,
                "impact": email.impact,
                "confidence": email.confidence,
                "recommended_action": email.recommended_action,
                "thread_id": email.thread_id,
                "created_at": email.created_at.isoformat()
            }
        
        drafts_with_context.append(draft_dict)
    
    return drafts_with_context


@router.get("/{draft_id}", response_model=dict)
async def get_draft(
    draft_id: str,
    db: AsyncSession = Depends(get_db)
):
    """
    Get draft by ID with email and company context
    No auth required - n8n calls this directly, but admin can also use it
    """
    from models.email import Email
    from models.company import Company
    
    result = await db.execute(
        select(Draft, Email, Company)
        .join(Email, Draft.email_id == Email.id, isouter=True)
        .join(Company, Draft.company_id == Company.company_id)
        .where(Draft.id == uuid.UUID(draft_id))
    )
    row = result.first()
    
    if not row:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Draft not found"
        )
    
    draft, email, company = row
    
    draft_dict = {
        "id": str(draft.id),
        "company_id": str(draft.company_id),
        "email_id": str(draft.email_id) if draft.email_id else None,
        "subject": draft.subject,
        "body": draft.body,
        "status": draft.status,
        "version": draft.version,
        "template_used": draft.template_used,
        "variables_used": draft.variables_used,
        "is_edited": draft.is_edited,
        "original_body": draft.original_body,
        "created_at": draft.created_at.isoformat(),
        "company_name": company.name if company else None,
        "company_email": company.email if company else None,
    }
    
    # Add email context if available (include trigger_type, recipient_context for follow-up UI)
    if email:
        rc = email.recipient_context
        if hasattr(rc, "__iter__") and not isinstance(rc, (str, bytes)):
            pass
        elif isinstance(rc, str):
            try:
                import json
                rc = json.loads(rc) if rc else None
            except Exception:
                rc = None
        draft_dict["email"] = {
            "id": str(email.id),
            "subject": email.subject,
            "from_email": email.from_email,
            "to_email": email.to_email,
            "email_type": email.email_type,
            "trigger_type": getattr(email, "trigger_type", None),
            "recipient_context": rc,
            "body": email.body,
            "priority_score": email.priority_score,
            "executive_summary": email.executive_summary,
            "function": email.function,
            "intent": email.intent,
            "urgency": email.urgency,
            "impact": email.impact,
            "confidence": email.confidence,
            "recommended_action": email.recommended_action,
            "thread_id": email.thread_id,
            "created_at": email.created_at.isoformat()
        }
    
    return draft_dict


@router.get("/{draft_id}/status", response_model=DraftStatusResponse)
async def get_draft_status(
    draft_id: str,
    db: AsyncSession = Depends(get_db)
):
    """Get draft status (called by n8n to check approval)"""
    result = await db.execute(
        select(Draft).where(Draft.id == uuid.UUID(draft_id))
    )
    draft = result.scalar_one_or_none()
    
    if not draft:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Draft not found"
        )
    
    return DraftStatusResponse(
        id=draft.id,
        status=draft.status,
        approved_by=draft.approved_by,
        approved_at=draft.approved_at,
        sent_at=draft.sent_at
    )


@router.post("/{draft_id}/ai-edit", response_model=DraftAIEditResponse)
async def ai_edit_draft(
    draft_id: str,
    body: DraftAIEditRequest,
    db: AsyncSession = Depends(get_db),
    admin: Admin = Depends(get_current_admin)
):
    """
    Edit draft with AI based on natural language instruction (admin only).
    Returns edited subject and body; no persistence until user approves.
    """
    result = await db.execute(
        select(Draft).where(Draft.id == uuid.UUID(draft_id))
    )
    draft = result.scalar_one_or_none()
    if not draft:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Draft not found"
        )
    if draft.status == "sent":
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Cannot edit a draft that has already been sent"
        )
    # Use current content from frontend when provided (incremental edits); otherwise use persisted draft
    subject_base = (body.current_subject or "").strip() or draft.subject
    body_base = (body.current_body or "").strip() if body.current_body is not None else draft.body
    if not body_base:
        body_base = draft.body

    # Load company brand context (Redis cache → Drive) so AI edits adhere to brand guidelines
    brand_context = None
    if draft.company_id:
        try:
            from services.brand_context_loader import brand_context_loader
            brand_context = await brand_context_loader.load_all(db, str(draft.company_id))
        except Exception as e:
            logger.warning(f"Could not load brand context for draft company {draft.company_id}: {e}. Proceeding without it.")

    try:
        edited_subject, edited_body = await edit_draft_with_ai(
            subject=subject_base,
            body=body_base,
            instruction=body.instruction,
            brand_context=brand_context,
        )
    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail=str(e)
        )
    except Exception as e:
        logger.exception("AI edit draft failed")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"AI edit failed: {str(e)}"
        )
    return DraftAIEditResponse(subject=edited_subject, body=edited_body)


@router.post("/{draft_id}/approve")
async def approve_draft(
    draft_id: str,
    approve_data: DraftApproveRequest,
    db: AsyncSession = Depends(get_db),
    admin: Admin = Depends(get_current_admin)
):
    """Approve draft for sending (admin only)"""
    result = await db.execute(
        select(Draft).where(Draft.id == uuid.UUID(draft_id))
    )
    draft = result.scalar_one_or_none()
    
    if not draft:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Draft not found"
        )
    
    # Update draft if edited
    if approve_data.edited_body and approve_data.edited_body != draft.body:
        # Save original body before editing (if not already saved)
        if not draft.original_body:
            draft.original_body = draft.body
        draft.body = approve_data.edited_body
        draft.is_edited = True
    if approve_data.edited_subject is not None and approve_data.edited_subject.strip() != draft.subject:
        draft.subject = approve_data.edited_subject.strip()

    # Approve draft
    draft.status = "approved"
    draft.approved_by = admin.id
    draft.approved_at = datetime.utcnow()
    
    await db.commit()
    await db.refresh(draft)
    
    # Log approval
    await audit_logger_service.log_draft_approved(
        db=db,
        company_id=str(draft.company_id),
        draft_id=str(draft.id),
        approved_by=str(admin.id)
    )
    
    return {
        "draft_id": str(draft.id),
        "status": "approved",
        "message": "Draft approved and ready to send"
    }


@router.get("/", response_model=list[dict])
async def list_drafts(
    company_id: Optional[str] = Query(None, description="Filter by company ID"),
    status: Optional[str] = Query(None, description="Filter by status (pending/approved/rejected/sent)"),
    limit: int = Query(50, ge=1, le=100, description="Number of results"),
    db: AsyncSession = Depends(get_db),
    admin: Admin = Depends(get_current_admin)
):
    """
    List drafts with optional filters (admin only).
    Returns drafts with email and company context (trigger_type, recipient_context for follow-up UI).
    """
    from uuid import UUID
    from models.company import Company
    
    query = (
        select(Draft, Email, Company)
        .join(Email, Draft.email_id == Email.id, isouter=True)
        .join(Company, Draft.company_id == Company.company_id)
    )
    
    if company_id:
        try:
            query = query.where(Draft.company_id == UUID(company_id))
        except ValueError:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Invalid company_id format"
            )
    if status:
        query = query.where(Draft.status == status)
    
    query = query.order_by(desc(Draft.created_at)).limit(limit)
    
    result = await db.execute(query)
    rows = result.all()
    
    out = []
    for draft, email, company in rows:
        draft_dict = {
            "id": str(draft.id),
            "company_id": str(draft.company_id),
            "email_id": str(draft.email_id) if draft.email_id else None,
            "subject": draft.subject,
            "body": draft.body,
            "status": draft.status,
            "version": draft.version,
            "template_used": draft.template_used,
            "created_at": draft.created_at.isoformat() if draft.created_at else None,
            "company_name": company.name if company else None,
            "company_email": company.email if company else None,
        }
        if email:
            rc = email.recipient_context
            if isinstance(rc, str):
                try:
                    import json
                    rc = json.loads(rc) if rc else None
                except Exception:
                    rc = None
            draft_dict["email"] = {
                "id": str(email.id),
                "subject": email.subject,
                "from_email": email.from_email,
                "to_email": email.to_email,
                "email_type": email.email_type,
                "trigger_type": getattr(email, "trigger_type", None),
                "recipient_context": rc,
                "body": email.body,
                "priority_score": email.priority_score,
                "executive_summary": email.executive_summary,
                "function": email.function,
                "intent": email.intent,
                "urgency": email.urgency,
                "impact": email.impact,
                "confidence": email.confidence,
                "recommended_action": email.recommended_action,
                "thread_id": email.thread_id,
                "created_at": email.created_at.isoformat() if email.created_at else None,
            }
        out.append(draft_dict)
    
    return out


@router.post("/{draft_id}/reject")
async def reject_draft(
    draft_id: str,
    db: AsyncSession = Depends(get_db),
    admin: Admin = Depends(get_current_admin)
):
    """Reject a draft (admin only)"""
    result = await db.execute(
        select(Draft).where(Draft.id == uuid.UUID(draft_id))
    )
    draft = result.scalar_one_or_none()
    
    if not draft:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Draft not found"
        )
    
    draft.status = "rejected"
    draft.approved_by = admin.id
    draft.approved_at = datetime.utcnow()
    
    await db.commit()
    await db.refresh(draft)
    
    await audit_logger_service.log(
        db=db,
        action_type="draft_rejected",
        action_description="Draft rejected by admin",
        company_id=str(draft.company_id),
        draft_id=str(draft.id),
        approved_by=str(admin.id),
        approval_status="rejected"
    )
    
    return {
        "draft_id": str(draft.id),
        "status": "rejected",
        "message": "Draft rejected"
    }


@router.post("/{draft_id}/sent")
async def mark_draft_sent(
    draft_id: str,
    body: Optional[DraftSentRequest] = None,
    db: AsyncSession = Depends(get_db)
):
    """
    Mark draft as sent (called by n8n after successfully sending email).
    Optional body: thread_id, gmail_message_id — persist on email for threading (e.g. outbound first send).
    No auth required - n8n calls this directly.
    """
    result = await db.execute(
        select(Draft).where(Draft.id == uuid.UUID(draft_id))
    )
    draft = result.scalar_one_or_none()
    
    if not draft:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Draft not found"
        )
    
    draft.status = "sent"
    draft.sent_at = datetime.utcnow()
    
    # Persist thread_id / gmail_message_id on email when provided (n8n sends after Gmail API)
    if body and (body.thread_id or body.gmail_message_id):
        email_result = await db.execute(
            select(Email).where(Email.id == draft.email_id)
        )
        email = email_result.scalar_one_or_none()
        if email:
            if body.thread_id:
                email.thread_id = body.thread_id.strip()
            if body.gmail_message_id:
                email.gmail_message_id = body.gmail_message_id.strip()
    
    await db.commit()
    await db.refresh(draft)
    
    await audit_logger_service.log(
        db=db,
        action_type="draft_sent",
        action_description="Draft sent via email",
        company_id=str(draft.company_id),
        draft_id=str(draft.id)
    )
    
    return {
        "draft_id": str(draft.id),
        "status": "sent",
        "sent_at": draft.sent_at.isoformat(),
        "message": "Draft marked as sent"
    }

