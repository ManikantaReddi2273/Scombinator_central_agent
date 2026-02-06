"""
Draft model
"""
from sqlalchemy import Column, String, Text, DateTime, ForeignKey, Boolean
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.sql import func
from sqlalchemy.orm import relationship
import uuid
from database import Base


class Draft(Base):
    """Draft model - stores AI-generated email drafts"""
    
    __tablename__ = "drafts"
    
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    company_id = Column(UUID(as_uuid=True), ForeignKey("companies.company_id"), nullable=False, index=True)
    email_id = Column(UUID(as_uuid=True), ForeignKey("emails.id"), nullable=True, index=True)
    
    # Draft content
    subject = Column(String(500), nullable=False)
    body = Column(Text, nullable=False)
    
    # Status
    status = Column(String(50), default="pending", nullable=False, index=True)  # pending/approved/rejected/sent
    approved_by = Column(UUID(as_uuid=True), nullable=True)  # Admin ID who approved
    approved_at = Column(DateTime(timezone=True), nullable=True)
    
    # Version tracking
    version = Column(String(10), default="1.0", nullable=False)
    is_edited = Column(Boolean, default=False, nullable=False)
    original_body = Column(Text, nullable=True)  # Original AI-generated body
    
    # Template info
    template_used = Column(String(255), nullable=True)
    variables_used = Column(Text, nullable=True)  # JSON string
    
    # Metadata
    created_at = Column(DateTime(timezone=True), server_default=func.now(), nullable=False, index=True)
    updated_at = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now(), nullable=False)
    sent_at = Column(DateTime(timezone=True), nullable=True)
    
    # Relationships
    company = relationship("Company", back_populates="drafts")
    email = relationship("Email", back_populates="drafts")
    
    def __repr__(self):
        return f"<Draft(id={self.id}, company_id={self.company_id}, status={self.status})>"

