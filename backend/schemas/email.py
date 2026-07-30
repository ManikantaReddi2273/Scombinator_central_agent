"""
Email schemas
"""
from pydantic import BaseModel
from typing import Optional, Dict, Any
from uuid import UUID
from datetime import datetime


class EmailProcessRequest(BaseModel):
    """Email processing request from n8n"""
    # Legacy n8n credential mapping (optional when company_id is provided)
    credential_id: Optional[str] = None
    # Preferred when OAuth was connected via backend callback (no n8n credential)
    company_id: Optional[str] = None
    email_data: Dict[str, Any]
    # email_data contains: subject, body, from, to, thread_id, gmail_message_id, etc.


class EmailClassification(BaseModel):
    """Email classification schema"""
    function: Optional[str] = None
    intent: Optional[str] = None
    urgency: Optional[str] = None
    impact: Optional[str] = None
    confidence: Optional[str] = None
    priority_score: Optional[str] = None


class EmailResponse(BaseModel):
    """Email response schema"""
    id: UUID
    company_id: UUID
    subject: str
    from_email: str
    to_email: str
    thread_id: Optional[str] = None
    gmail_message_id: Optional[str] = None  # Gmail message ID for threading
    thread_history: list = []  # Previous emails in thread
    thread_count: int = 0  # Number of previous emails
    email_type: Optional[str] = None  # "inbound" or "outbound"
    recipient_context: Optional[Dict[str, Any]] = None  # For outbound: lead_id, name, company, etc. (for CRM update)
    function: Optional[str]
    intent: Optional[str]
    priority_score: Optional[str]
    executive_summary: Optional[str]
    recommended_action: Optional[str]
    created_at: datetime
    
    class Config:
        from_attributes = True


class EmailListResponse(BaseModel):
    """Email list response with company info"""
    email_id: str
    company_id: str
    company_name: str
    subject: str
    from_email: str
    priority_score: Optional[str]
    executive_summary: Optional[str]
    created_at: datetime

