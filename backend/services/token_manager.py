"""
Token manager service for Google OAuth tokens
"""
from datetime import datetime, timedelta
from typing import Optional
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from models.company import Company
from services.encryption import encryption_service
from google.oauth2.credentials import Credentials
from google.auth.transport.requests import Request
from googleapiclient.discovery import build
import json


class TokenManagerService:
    """Service for managing Google OAuth tokens"""
    
    def __init__(self):
        self.encryption_service = encryption_service
    
    async def store_tokens(
        self,
        db: AsyncSession,
        company_id: str,
        access_token: str,
        refresh_token: str,
        expires_in: int = 3600,
        n8n_credential_id: Optional[str] = None
    ) -> Company:
        """Store encrypted tokens for a company"""
        from uuid import UUID
        
        # Convert company_id to UUID if string
        if isinstance(company_id, str):
            company_id = UUID(company_id)
        
        # Encrypt tokens
        encrypted_access = self.encryption_service.encrypt(access_token)
        encrypted_refresh = self.encryption_service.encrypt(refresh_token)
        
        # Calculate expiration
        expires_at = datetime.utcnow() + timedelta(seconds=expires_in)
        
        # Update company record
        result = await db.execute(
            select(Company).where(Company.company_id == company_id)
        )
        company = result.scalar_one_or_none()
        
        if company:
            company.encrypted_access_token = encrypted_access
            company.encrypted_refresh_token = encrypted_refresh
            company.access_token_expires_at = expires_at
            if n8n_credential_id:
                company.n8n_credential_id = n8n_credential_id
            await db.commit()
            await db.refresh(company)
            return company
        else:
            raise ValueError(f"Company {company_id} not found")
    
    async def get_valid_token(self, db: AsyncSession, company_id: str) -> str:
        """Get valid access token, refreshing if needed"""
        from uuid import UUID
        
        # Convert company_id to UUID if string
        if isinstance(company_id, str):
            company_id = UUID(company_id)
        
        result = await db.execute(
            select(Company).where(Company.company_id == company_id)
        )
        company = result.scalar_one_or_none()
        
        if not company:
            raise ValueError(f"Company {company_id} not found")
        
        # Check if token is expired or expiring soon (within 5 minutes)
        now = datetime.utcnow()
        expires_at = company.access_token_expires_at
        
        if not expires_at or (expires_at - now).total_seconds() < 300:
            # Token expired or expiring soon, refresh it
            await self._refresh_token(db, company)
            # Reload company to get new token
            await db.refresh(company)
        
        # Decrypt and return access token
        return self.encryption_service.decrypt(company.encrypted_access_token)
    
    async def _refresh_token(self, db: AsyncSession, company: Company) -> None:
        """Refresh access token using refresh token"""
        # Decrypt refresh token
        refresh_token = self.encryption_service.decrypt(company.encrypted_refresh_token)
        
        # Create credentials object
        creds = Credentials(
            token=None,
            refresh_token=refresh_token,
            token_uri="https://oauth2.googleapis.com/token",
            client_id=None,  # Not needed for refresh
            client_secret=None  # Not needed for refresh
        )
        
        # Refresh the token
        creds.refresh(Request())
        
        # Encrypt and store new token
        company.encrypted_access_token = self.encryption_service.encrypt(creds.token)
        if creds.expiry:
            company.access_token_expires_at = creds.expiry
        
        await db.commit()
    
    async def get_credentials(self, db: AsyncSession, company_id: str) -> Credentials:
        """Get Google credentials object for API calls"""
        from uuid import UUID
        
        # Convert company_id to UUID if string
        if isinstance(company_id, str):
            company_id = UUID(company_id)
        
        access_token = await self.get_valid_token(db, str(company_id))
        
        result = await db.execute(
            select(Company).where(Company.company_id == company_id)
        )
        company = result.scalar_one_or_none()
        
        if not company:
            raise ValueError(f"Company {company_id} not found")
        
        refresh_token = self.encryption_service.decrypt(company.encrypted_refresh_token)
        
        return Credentials(
            token=access_token,
            refresh_token=refresh_token,
            token_uri="https://oauth2.googleapis.com/token"
        )


# Singleton instance
token_manager_service = TokenManagerService()

