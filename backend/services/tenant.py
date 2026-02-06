"""
Tenant service for company/tenant management
"""
from typing import Optional
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from models.company import Company
from services.token_manager import token_manager_service
import uuid


class TenantService:
    """Service for tenant/company management"""
    
    def __init__(self):
        self.token_manager = token_manager_service
    
    async def get_company_by_credential_id(
        self,
        db: AsyncSession,
        n8n_credential_id: str
    ) -> Optional[Company]:
        """Get company by n8n credential ID"""
        result = await db.execute(
            select(Company).where(Company.n8n_credential_id == n8n_credential_id)
        )
        return result.scalar_one_or_none()
    
    async def get_company_by_email(
        self,
        db: AsyncSession,
        email: str
    ) -> Optional[Company]:
        """Get company by email address"""
        result = await db.execute(
            select(Company).where(Company.email == email)
        )
        return result.scalar_one_or_none()
    
    async def get_company_by_name(
        self,
        db: AsyncSession,
        name: str
    ) -> Optional[Company]:
        """Get company by name"""
        result = await db.execute(
            select(Company).where(Company.name == name)
        )
        return result.scalar_one_or_none()
    
    async def get_company_by_id(
        self,
        db: AsyncSession,
        company_id: str
    ) -> Optional[Company]:
        """Get company by company_id"""
        result = await db.execute(
            select(Company).where(Company.company_id == company_id)
        )
        return result.scalar_one_or_none()
    
    async def create_company_without_tokens(
        self,
        db: AsyncSession,
        name: str,
        email: str
    ) -> Company:
        """Create a new company without OAuth tokens (Step 1)"""
        company_id = uuid.uuid4()
        
        # Create company without tokens
        company = Company(
            company_id=company_id,
            name=name,
            email=email,
            encrypted_access_token=None,
            encrypted_refresh_token=None,
            n8n_credential_id=None,
            status="active"
        )
        
        db.add(company)
        await db.commit()
        await db.refresh(company)
        
        return company
    
    async def connect_oauth_to_company(
        self,
        db: AsyncSession,
        company_id: str,
        access_token: str,
        refresh_token: str,
        n8n_credential_id: Optional[str] = None,
        expires_in: int = 3600
    ) -> Company:
        """Connect OAuth tokens to an existing company (Step 2)"""
        from services.encryption import encryption_service
        
        # Get company
        company = await self.get_company_by_id(db, company_id)
        if not company:
            raise ValueError(f"Company with id {company_id} not found")
        
        # Encrypt tokens
        encrypted_access = encryption_service.encrypt(access_token)
        encrypted_refresh = encryption_service.encrypt(refresh_token)
        
        # Update company with tokens
        company.encrypted_access_token = encrypted_access
        company.encrypted_refresh_token = encrypted_refresh
        company.n8n_credential_id = n8n_credential_id
        
        await db.commit()
        await db.refresh(company)
        
        # Store token expiration
        await self.token_manager.store_tokens(
            db,
            str(company.company_id),
            access_token,
            refresh_token,
            expires_in,
            n8n_credential_id
        )
        
        return company
    
    async def create_company(
        self,
        db: AsyncSession,
        name: str,
        email: str,
        access_token: str,
        refresh_token: str,
        n8n_credential_id: Optional[str] = None,
        expires_in: int = 3600
    ) -> Company:
        """Create a new company with encrypted tokens (backward compatibility)"""
        from services.encryption import encryption_service
        
        # Generate company_id (format: SC-001, SC-002, etc.)
        # In production, use proper UUID or sequential ID
        company_id = uuid.uuid4()
        
        # Encrypt tokens
        encrypted_access = encryption_service.encrypt(access_token)
        encrypted_refresh = encryption_service.encrypt(refresh_token)
        
        # Create company
        company = Company(
            company_id=company_id,
            name=name,
            email=email,
            encrypted_access_token=encrypted_access,
            encrypted_refresh_token=encrypted_refresh,
            n8n_credential_id=n8n_credential_id,
            status="active"
        )
        
        db.add(company)
        await db.commit()
        await db.refresh(company)
        
        # Store token expiration
        await self.token_manager.store_tokens(
            db,
            str(company.company_id),
            access_token,
            refresh_token,
            expires_in,
            n8n_credential_id
        )
        
        return company
    
    async def map_credential_to_company(
        self,
        db: AsyncSession,
        credential_id: str
    ) -> Optional[str]:
        """Map n8n credential_id to company_id"""
        company = await self.get_company_by_credential_id(db, credential_id)
        if company:
            return str(company.company_id)
        return None


# Singleton instance
tenant_service = TenantService()

