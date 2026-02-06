"""
Pydantic schemas for request/response validation
"""
from .auth import LoginRequest, LoginResponse, TokenData
from .company import CompanyCreate, CompanyResponse, CompanyRegisterRequest
from .email import EmailProcessRequest, EmailResponse, EmailClassification
from .draft import DraftResponse, DraftStatusResponse, DraftApproveRequest

__all__ = [
    "LoginRequest",
    "LoginResponse",
    "TokenData",
    "CompanyCreate",
    "CompanyResponse",
    "CompanyRegisterRequest",
    "EmailProcessRequest",
    "EmailResponse",
    "EmailClassification",
    "DraftResponse",
    "DraftStatusResponse",
    "DraftApproveRequest",
]

