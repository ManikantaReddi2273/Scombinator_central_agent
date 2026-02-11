"""
Draft management routes
"""
from fastapi import APIRouter, Depends, HTTPException, status, Query
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, desc
from database import get_db
from models.admin import Admin
from models.draft import Draft
from schemas.draft import DraftResponse, DraftStatusResponse, DraftApproveRequest
from services.audit_logger import audit_logger_service
from auth.jwt import get_current_admin
from datetime import datetime
from typing import Optional
import uuid

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
        
        # Add email context if available
        if email:
            draft_dict["email"] = {
                "id": str(email.id),
                "subject": email.subject,
                "from_email": email.from_email,
                "to_email": email.to_email,
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
    
    # Add email context if available
    if email:
        draft_dict["email"] = {
            "id": str(email.id),
            "subject": email.subject,
            "from_email": email.from_email,
            "to_email": email.to_email,
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


@router.get("/", response_model=list[DraftResponse])
async def list_drafts(
    company_id: Optional[str] = Query(None, description="Filter by company ID"),
    status: Optional[str] = Query(None, description="Filter by status (pending/approved/rejected/sent)"),
    limit: int = Query(50, ge=1, le=100, description="Number of results"),
    db: AsyncSession = Depends(get_db),
    admin: Admin = Depends(get_current_admin)
):
    """
    List drafts with optional filters (admin only)
    Returns drafts sorted by creation date (newest first)
    """
    from uuid import UUID
    
    query = select(Draft)
    
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
    db: AsyncSession = Depends(get_db)
):
    """
    Mark draft as sent (called by n8n after successfully sending email)
    No auth required - n8n calls this directly
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
    
    # Update draft status
    draft.status = "sent"
    draft.sent_at = datetime.utcnow()
    
    await db.commit()
    await db.refresh(draft)
    
    # Log in audit_logs
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

