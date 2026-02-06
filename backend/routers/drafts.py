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


@router.get("/pending", response_model=list[DraftResponse])
async def get_pending_drafts(
    company_id: Optional[str] = Query(None, description="Filter by company ID"),
    limit: int = Query(20, ge=1, le=100, description="Number of results"),
    db: AsyncSession = Depends(get_db),
    admin: Admin = Depends(get_current_admin)
):
    """
    Get pending drafts awaiting approval (admin only)
    This is the main queue for admin review
    """
    from uuid import UUID
    
    query = select(Draft).where(Draft.status == "pending")
    
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


@router.get("/{draft_id}", response_model=DraftResponse)
async def get_draft(
    draft_id: str,
    db: AsyncSession = Depends(get_db),
    admin: Admin = Depends(get_current_admin)
):
    """Get draft by ID (admin only)"""
    result = await db.execute(
        select(Draft).where(Draft.id == uuid.UUID(draft_id))
    )
    draft = result.scalar_one_or_none()
    
    if not draft:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Draft not found"
        )
    
    return DraftResponse(
        id=draft.id,
        company_id=draft.company_id,
        email_id=draft.email_id,
        subject=draft.subject,
        body=draft.body,
        status=draft.status,
        version=draft.version,
        template_used=draft.template_used,
        created_at=draft.created_at
    )


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
    if approve_data.edited_body:
        draft.body = approve_data.edited_body
        draft.is_edited = True
        if not draft.original_body:
            draft.original_body = draft.body
    
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

