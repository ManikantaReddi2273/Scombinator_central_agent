"""
Email schemas
"""
from pydantic import BaseModel
from typing import Optional, Dict, Any
from uuid import UUID
from datetime import datetime


class EmailProcessRequest(BaseModel):
    """Email processing request from n8n"""
    credential_id: str
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

