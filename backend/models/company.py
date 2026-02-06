"""
Company model
"""
from sqlalchemy import Column, String, DateTime, Text, ForeignKey
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.sql import func
from sqlalchemy.orm import relationship
import uuid
from database import Base


class Company(Base):
    """Company model - represents each company/tenant"""
    
    __tablename__ = "companies"
    
    company_id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    name = Column(String(255), nullable=False, unique=True, index=True)
    email = Column(String(255), nullable=False, unique=True, index=True)
    
    # Encrypted tokens (stored as TEXT) - nullable for two-step registration
    encrypted_access_token = Column(Text, nullable=True)
    encrypted_refresh_token = Column(Text, nullable=True)
    access_token_expires_at = Column(DateTime(timezone=True), nullable=True)
    
    # n8n reference (for mapping)
    n8n_credential_id = Column(String(255), nullable=True, index=True)
    
    # Status
    status = Column(String(50), default="active", nullable=False, index=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now(), nullable=False)
    updated_at = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now(), nullable=False)
    
    # Relationships
    emails = relationship("Email", back_populates="company", cascade="all, delete-orphan")
    drafts = relationship("Draft", back_populates="company", cascade="all, delete-orphan")
    candidates = relationship("Candidate", back_populates="company", cascade="all, delete-orphan")
    logs = relationship("AuditLog", back_populates="company", cascade="all, delete-orphan")
    
    def __repr__(self):
        return f"<Company(company_id={self.company_id}, name={self.name}, email={self.email})>"

