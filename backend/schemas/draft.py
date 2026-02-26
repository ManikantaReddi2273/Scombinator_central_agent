"""
Draft schemas
"""
from pydantic import BaseModel
from typing import Optional
from uuid import UUID
from datetime import datetime


class DraftResponse(BaseModel):
    """Draft response schema"""
    id: UUID
    company_id: UUID
    email_id: Optional[UUID]
    subject: str
    body: str
    status: str
    version: str
    template_used: Optional[str]
    created_at: datetime
    
    class Config:
        from_attributes = True


class DraftStatusResponse(BaseModel):
    """Draft status response"""
    id: UUID
    status: str
    approved_by: Optional[UUID]
    approved_at: Optional[datetime]
    sent_at: Optional[datetime]


class DraftApproveRequest(BaseModel):
    """Draft approval request"""
    draft_id: UUID
    edited_body: Optional[str] = None  # If admin edited the draft


class DraftSentRequest(BaseModel):
    """Optional body when marking draft as sent (from n8n). Persists thread for outbound."""
    thread_id: Optional[str] = None
    gmail_message_id: Optional[str] = None

