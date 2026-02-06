"""
Audit logger service for tracking all system actions
"""
from typing import Optional, Dict, Any
from sqlalchemy.ext.asyncio import AsyncSession
from models.log import AuditLog
from datetime import datetime
import uuid


class AuditLoggerService:
    """Service for logging audit trails"""
    
    async def log(
        self,
        db: AsyncSession,
        action_type: str,
        action_description: str,
        company_id: Optional[str] = None,
        source: Optional[str] = None,
        template_used: Optional[str] = None,
        approved_by: Optional[str] = None,
        approval_status: Optional[str] = None,
        email_id: Optional[str] = None,
        draft_id: Optional[str] = None,
        candidate_id: Optional[str] = None,
        metadata: Optional[Dict[str, Any]] = None
    ) -> AuditLog:
        """Create an audit log entry"""
        log_entry = AuditLog(
            id=uuid.uuid4(),
            company_id=uuid.UUID(company_id) if company_id else None,
            action_type=action_type,
            action_description=action_description,
            source=source,
            template_used=template_used,
            approved_by=uuid.UUID(approved_by) if approved_by else None,
            approval_status=approval_status,
            email_id=uuid.UUID(email_id) if email_id else None,
            draft_id=uuid.UUID(draft_id) if draft_id else None,
            candidate_id=uuid.UUID(candidate_id) if candidate_id else None,
            extra_metadata=metadata,
            created_at=datetime.utcnow()
        )
        
        db.add(log_entry)
        await db.commit()
        await db.refresh(log_entry)
        
        return log_entry
    
    async def log_email_processed(
        self,
        db: AsyncSession,
        company_id: str,
        email_id: str,
        classification_metadata: Dict[str, Any]
    ):
        """Log email processing"""
        return await self.log(
            db=db,
            action_type="email_processed",
            action_description=f"Email processed and classified",
            company_id=company_id,
            email_id=email_id,
            metadata=classification_metadata
        )
    
    async def log_draft_created(
        self,
        db: AsyncSession,
        company_id: str,
        draft_id: str,
        template_used: Optional[str] = None
    ):
        """Log draft creation"""
        return await self.log(
            db=db,
            action_type="draft_created",
            action_description="Draft email created",
            company_id=company_id,
            draft_id=draft_id,
            template_used=template_used
        )
    
    async def log_draft_approved(
        self,
        db: AsyncSession,
        company_id: str,
        draft_id: str,
        approved_by: str
    ):
        """Log draft approval"""
        return await self.log(
            db=db,
            action_type="draft_approved",
            action_description="Draft approved for sending",
            company_id=company_id,
            draft_id=draft_id,
            approved_by=approved_by,
            approval_status="approved"
        )
    
    async def log_company_added(
        self,
        db: AsyncSession,
        company_id: str,
        company_name: str
    ):
        """Log company addition"""
        return await self.log(
            db=db,
            action_type="company_added",
            action_description=f"Company {company_name} added to platform",
            company_id=company_id,
            metadata={"company_name": company_name}
        )


# Singleton instance
audit_logger_service = AuditLoggerService()

