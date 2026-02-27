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
    edited_subject: Optional[str] = None  # If admin or AI edited the subject


class DraftAIEditRequest(BaseModel):
    """Request for AI-assisted draft edit. Use current_subject/current_body for incremental edits (latest accepted content)."""
    instruction: str  # Natural language editing instruction
    current_subject: Optional[str] = None  # If provided, use as base instead of DB draft (for incremental edits)
    current_body: Optional[str] = None  # If provided, use as base instead of DB draft (for incremental edits)


class DraftAIEditResponse(BaseModel):
    """Response from AI edit: edited subject and body"""
    subject: str
    body: str


class DraftSentRequest(BaseModel):
    """Optional body when marking draft as sent (from n8n). Persists thread for outbound."""
    thread_id: Optional[str] = None
    gmail_message_id: Optional[str] = None

