"""
Company schemas
"""
from pydantic import BaseModel, EmailStr
from typing import Optional
from datetime import datetime
from uuid import UUID


class CompanyRegisterRequest(BaseModel):
    """Company registration request from n8n"""
    company_name: str
    email: EmailStr
    access_token: str
    refresh_token: str
    n8n_credential_id: Optional[str] = None
    expires_in: Optional[int] = 3600


class CompanyCreate(BaseModel):
    """Company creation schema"""
    name: str
    email: EmailStr


class CompanyResponse(BaseModel):
    """Company response schema"""
    company_id: UUID
    name: str
    email: str
    n8n_credential_id: Optional[str]
    status: str
    created_at: datetime
    
    class Config:
        from_attributes = True

