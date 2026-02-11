"""
Dashboard statistics routes
"""
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, func, and_, cast, Integer
from database import get_db
from models.admin import Admin
from models.company import Company
from models.email import Email
from models.draft import Draft
from auth.jwt import get_current_admin
from pydantic import BaseModel
from typing import Optional

router = APIRouter(prefix="/api/dashboard", tags=["Dashboard"])


class DashboardStatsResponse(BaseModel):
    """Dashboard statistics response"""
    total_companies: int
    pending_drafts: int
    high_priority_emails: int
    total_emails: int


@router.get("/stats", response_model=DashboardStatsResponse)
async def get_dashboard_stats(
    db: AsyncSession = Depends(get_db),
    admin: Admin = Depends(get_current_admin)
):
    """
    Get aggregated dashboard statistics
    Returns:
    - total_companies: Total number of companies
    - pending_drafts: Number of drafts with status 'pending'
    - high_priority_emails: Number of emails with priority_score >= 80
    - total_emails: Total number of emails
    """
    try:
        # Count total companies
        companies_query = select(func.count(Company.company_id))
        companies_result = await db.execute(companies_query)
        total_companies = companies_result.scalar() or 0
        
        # Count pending drafts
        pending_drafts_query = select(func.count(Draft.id)).where(Draft.status == "pending")
        pending_drafts_result = await db.execute(pending_drafts_query)
        pending_drafts = pending_drafts_result.scalar() or 0
        
        # Count high priority emails (priority_score >= 80)
        # Note: priority_score is stored as string, so we need to cast it
        high_priority_query = select(func.count(Email.id)).where(
            and_(
                Email.priority_score.isnot(None),
                cast(Email.priority_score, Integer) >= 80
            )
        )
        high_priority_result = await db.execute(high_priority_query)
        high_priority_emails = high_priority_result.scalar() or 0
        
        # Count total emails
        total_emails_query = select(func.count(Email.id))
        total_emails_result = await db.execute(total_emails_query)
        total_emails = total_emails_result.scalar() or 0
        
        return DashboardStatsResponse(
            total_companies=total_companies,
            pending_drafts=pending_drafts,
            high_priority_emails=high_priority_emails,
            total_emails=total_emails
        )
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error fetching dashboard statistics: {str(e)}"
        )

