"""
Token manager service for Google OAuth tokens
"""
from datetime import datetime, timedelta, timezone
from typing import Optional
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from models.company import Company
from services.encryption import encryption_service
from google.oauth2.credentials import Credentials
from google.auth.transport.requests import Request
from googleapiclient.discovery import build
from config import settings
import json
import os
from pathlib import Path


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
        
        # Calculate expiration (use timezone-aware datetime)
        expires_at = datetime.now(timezone.utc) + timedelta(seconds=expires_in)
        
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
        now = datetime.now(timezone.utc)
        expires_at = company.access_token_expires_at
        
        # Handle timezone-aware and timezone-naive datetimes
        if expires_at:
            # If expires_at is timezone-naive, assume it's UTC
            if expires_at.tzinfo is None:
                expires_at = expires_at.replace(tzinfo=timezone.utc)
        
        if not expires_at or (expires_at - now).total_seconds() < 300:
            # Token expired or expiring soon, refresh it
            await self._refresh_token(db, company)
            # Reload company to get new token
            await db.refresh(company)
        
        # Decrypt and return access token
        return self.encryption_service.decrypt(company.encrypted_access_token)
    
    def _get_google_credentials(self) -> tuple[str, str]:
        """Get Google OAuth client_id and client_secret from config or JSON file"""
        # Try to get from environment variables first
        client_id = settings.GOOGLE_CLIENT_ID
        client_secret = settings.GOOGLE_CLIENT_SECRET
        
        # Check if credentials are valid (not None and not placeholder values)
        is_valid = (
            client_id and 
            client_secret and 
            client_id != "your-google-client-id" and 
            client_secret != "your-google-client-secret"
        )
        
        # If not valid from env, try to read from JSON file
        if not is_valid:
            # Try multiple possible paths for the JSON file
            # __file__ is backend/services/token_manager.py
            # So parent.parent.parent should be project root
            possible_paths = [
                Path(__file__).parent.parent.parent / "scombinator_creditional_google_oauth.json",  # From backend/services/ -> project root
                Path(__file__).parent.parent / "scombinator_creditional_google_oauth.json",  # From backend/services/ -> backend/
                Path.cwd() / "scombinator_creditional_google_oauth.json",  # Current working directory
                Path.cwd().parent / "scombinator_creditional_google_oauth.json",  # Parent of current directory
            ]
            json_path = None
            for path in possible_paths:
                if path.exists():
                    json_path = path
                    break
            
            if json_path:
                try:
                    with open(json_path, 'r') as f:
                        oauth_config = json.load(f)
                        client_id = oauth_config.get("web", {}).get("client_id")
                        client_secret = oauth_config.get("web", {}).get("client_secret")
                except Exception as e:
                    import logging
                    logger = logging.getLogger(__name__)
                    logger.error(f"Error reading OAuth JSON file: {str(e)}")
                    pass
        
        if not client_id or not client_secret:
            raise ValueError(
                "GOOGLE_CLIENT_ID and GOOGLE_CLIENT_SECRET must be set in environment variables "
                "or in scombinator_creditional_google_oauth.json file"
            )
        
        return client_id, client_secret
    
    async def _refresh_token(self, db: AsyncSession, company: Company) -> None:
        """Refresh access token using refresh token"""
        # Decrypt refresh token
        refresh_token = self.encryption_service.decrypt(company.encrypted_refresh_token)
        
        # Get client_id and client_secret
        client_id, client_secret = self._get_google_credentials()
        
        # Create credentials object with all required fields
        creds = Credentials(
            token=None,
            refresh_token=refresh_token,
            token_uri="https://oauth2.googleapis.com/token",
            client_id=client_id,
            client_secret=client_secret
        )
        
        # Refresh the token
        creds.refresh(Request())
        
        # Encrypt and store new token
        company.encrypted_access_token = self.encryption_service.encrypt(creds.token)
        if creds.expiry:
            # Ensure expiry is timezone-aware
            if creds.expiry.tzinfo is None:
                company.access_token_expires_at = creds.expiry.replace(tzinfo=timezone.utc)
            else:
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

