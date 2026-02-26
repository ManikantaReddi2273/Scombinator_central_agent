"""
Email model
"""
from sqlalchemy import Column, String, Text, DateTime, JSON, ForeignKey
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.sql import func
from sqlalchemy.orm import relationship
import uuid
from database import Base


class Email(Base):
    """Email model - stores inbound/outbound emails"""
    
    __tablename__ = "emails"
    
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    company_id = Column(UUID(as_uuid=True), ForeignKey("companies.company_id"), nullable=False, index=True)
    
    # Email data
    subject = Column(String(500), nullable=False)
    body = Column(Text, nullable=False)
    from_email = Column(String(255), nullable=False, index=True)
    to_email = Column(String(255), nullable=False, index=True)
    thread_id = Column(String(255), nullable=True, index=True)
    gmail_message_id = Column(String(255), nullable=True, unique=True, index=True)
    
    # Classification (from AI)
    function = Column(String(50), nullable=True)  # Sales/Hiring/Legal/Support/etc
    intent = Column(String(50), nullable=True)  # Inquiry/Follow-up/Objection/etc
    urgency = Column(String(50), nullable=True)  # Immediate/Soon/Can wait
    impact = Column(String(50), nullable=True)  # Revenue/Hiring/Brand/Low
    confidence = Column(String(50), nullable=True)  # Clear/Ambiguous/Missing info
    priority_score = Column(String(10), nullable=True, index=True)  # 0-100
    
    # Summary and recommendation
    executive_summary = Column(Text, nullable=True)
    recommended_action = Column(String(100), nullable=True)
    
    # Metadata
    classification_metadata = Column(JSON, nullable=True)  # Full AI response
    created_at = Column(DateTime(timezone=True), server_default=func.now(), nullable=False, index=True)
    updated_at = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now(), nullable=False)
    
    # Outbound email fields
    email_type = Column(String(20), nullable=True, default="inbound", index=True)  # "inbound" or "outbound"
    outbound_intent = Column(String(100), nullable=True)  # followup_checkin, schedule_meeting, send_proposal, address_objection
    outbound_sequence_step = Column(String(10), nullable=True)  # For B2C sequences (B2B uses null)
    recipient_context = Column(JSON, nullable=True)  # Stores lead/recipient data from CRM
    scheduled_send_at = Column(DateTime(timezone=True), nullable=True)  # For scheduled emails
    trigger_type = Column(String(50), nullable=True)  # manual, time_based, calendar, task
    
    # Relationships
    company = relationship("Company", back_populates="emails")
    drafts = relationship("Draft", back_populates="email", cascade="all, delete-orphan")
    
    def __repr__(self):
        return f"<Email(id={self.id}, company_id={self.company_id}, subject={self.subject[:50]})>"

