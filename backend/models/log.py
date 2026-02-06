"""
Audit log model
"""
from sqlalchemy import Column, String, Text, DateTime, ForeignKey, JSON
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.sql import func
from sqlalchemy.orm import relationship
import uuid
from database import Base


class AuditLog(Base):
    """Audit log model - tracks all system actions"""
    
    __tablename__ = "audit_logs"
    
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    company_id = Column(UUID(as_uuid=True), ForeignKey("companies.company_id"), nullable=True, index=True)
    
    # Action details
    action_type = Column(String(100), nullable=False, index=True)  # email_processed/draft_approved/company_added/etc
    action_description = Column(Text, nullable=True)
    
    # Source tracking
    source = Column(String(255), nullable=True)  # Which template/snippet was used
    template_used = Column(String(255), nullable=True)
    
    # Approval tracking
    approved_by = Column(UUID(as_uuid=True), nullable=True)  # Admin ID
    approval_status = Column(String(50), nullable=True)  # approved/rejected/pending
    
    # Related entities
    email_id = Column(UUID(as_uuid=True), nullable=True, index=True)
    draft_id = Column(UUID(as_uuid=True), nullable=True, index=True)
    candidate_id = Column(UUID(as_uuid=True), nullable=True, index=True)
    
    # Metadata (renamed to avoid SQLAlchemy conflict)
    extra_metadata = Column(JSON, nullable=True)  # Additional context
    created_at = Column(DateTime(timezone=True), server_default=func.now(), nullable=False, index=True)
    
    # Relationships
    company = relationship("Company", back_populates="logs")
    
    def __repr__(self):
        return f"<AuditLog(id={self.id}, action_type={self.action_type}, company_id={self.company_id})>"

