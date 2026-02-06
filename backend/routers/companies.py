"""
Company management routes
"""
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from database import get_db
from models.admin import Admin
from models.company import Company
from schemas.company import CompanyRegisterRequest, CompanyResponse, CompanyCreate, OAuthConnectRequest
from services.tenant import tenant_service
from services.audit_logger import audit_logger_service
from auth.jwt import get_current_admin
import traceback

router = APIRouter(prefix="/api/companies", tags=["Companies"])


@router.post("/", response_model=CompanyResponse)
async def create_company(
    company_data: CompanyCreate,
    db: AsyncSession = Depends(get_db),
    admin: Admin = Depends(get_current_admin)
):
    """
    Create a new company without OAuth tokens (Step 1)
    Admin can register company with just name and email.
    OAuth can be connected later via /connect-oauth endpoint.
    """
    # Check if company with same name already exists
    existing_by_name = await tenant_service.get_company_by_name(db, company_data.name)
    if existing_by_name:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Company with name '{company_data.name}' already exists"
        )
    
    # Check if company with same email already exists
    existing_by_email = await tenant_service.get_company_by_email(db, company_data.email)
    if existing_by_email:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Company with email {company_data.email} already exists"
        )
    
    # Create company without tokens
    company = await tenant_service.create_company_without_tokens(
        db=db,
        name=company_data.name,
        email=company_data.email
    )
    
    # Log company addition
    await audit_logger_service.log_company_added(
        db=db,
        company_id=str(company.company_id),
        company_name=company.name
    )
    
    return CompanyResponse(
        company_id=company.company_id,
        name=company.name,
        email=company.email,
        n8n_credential_id=company.n8n_credential_id,
        status=company.status,
        created_at=company.created_at,
        has_oauth_connected=company.encrypted_access_token is not None
    )


@router.post("/{company_id}/connect-oauth", response_model=CompanyResponse)
async def connect_oauth(
    company_id: str,
    oauth_data: OAuthConnectRequest,
    db: AsyncSession = Depends(get_db)
):
    """
    Connect OAuth tokens to an existing company (Step 2)
    This endpoint is called by n8n after OAuth flow completes.
    No admin auth required - n8n calls this directly.
    """
    # Check if company exists
    company = await tenant_service.get_company_by_id(db, company_id)
    if not company:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Company with id {company_id} not found"
        )
    
    # Check if OAuth already connected
    if company.encrypted_access_token is not None:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Company {company_id} already has OAuth tokens connected. Use update endpoint to refresh tokens."
        )
    
    # Connect OAuth tokens
    try:
        company = await tenant_service.connect_oauth_to_company(
            db=db,
            company_id=company_id,
            access_token=oauth_data.access_token,
            refresh_token=oauth_data.refresh_token,
            n8n_credential_id=oauth_data.n8n_credential_id,
            expires_in=oauth_data.expires_in or 3600
        )
    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=str(e)
        )
    
    return CompanyResponse(
        company_id=company.company_id,
        name=company.name,
        email=company.email,
        n8n_credential_id=company.n8n_credential_id,
        status=company.status,
        created_at=company.created_at,
        has_oauth_connected=True
    )


@router.post("/register", response_model=CompanyResponse)
async def register_company(
    company_data: CompanyRegisterRequest,
    db: AsyncSession = Depends(get_db)
):
    """
    Register a new company (called by n8n after OAuth)
    This endpoint receives tokens from n8n and creates company record
    """
    # Check if company with same name already exists
    existing_by_name = await tenant_service.get_company_by_name(db, company_data.company_name)
    if existing_by_name:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Company with name '{company_data.company_name}' already exists"
        )
    
    # Check if company with same email already exists
    existing_by_email = await tenant_service.get_company_by_email(db, company_data.email)
    if existing_by_email:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Company with email {company_data.email} already exists"
        )
    
    # Create company
    company = await tenant_service.create_company(
        db=db,
        name=company_data.company_name,
        email=company_data.email,
        access_token=company_data.access_token,
        refresh_token=company_data.refresh_token,
        n8n_credential_id=company_data.n8n_credential_id,
        expires_in=company_data.expires_in or 3600
    )
    
    # Log company addition
    await audit_logger_service.log_company_added(
        db=db,
        company_id=str(company.company_id),
        company_name=company.name
    )
    
    return CompanyResponse(
        company_id=company.company_id,
        name=company.name,
        email=company.email,
        n8n_credential_id=company.n8n_credential_id,
        status=company.status,
        created_at=company.created_at,
        has_oauth_connected=company.encrypted_access_token is not None
    )


@router.get("/", response_model=list[CompanyResponse])
async def list_companies(
    db: AsyncSession = Depends(get_db),
    admin: Admin = Depends(get_current_admin)
):
    """List all companies (admin only)"""
    try:
        result = await db.execute(select(Company).order_by(Company.created_at.desc()))
        companies = result.scalars().all()
        
        return [
            CompanyResponse(
                company_id=c.company_id,
                name=c.name,
                email=c.email,
                n8n_credential_id=c.n8n_credential_id,
                status=c.status,
                created_at=c.created_at,
                has_oauth_connected=c.encrypted_access_token is not None
            )
            for c in companies
        ]
    except Exception as e:
        import logging
        logger = logging.getLogger(__name__)
        logger.error(f"Error listing companies: {str(e)}")
        logger.error(traceback.format_exc())
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error fetching companies: {str(e)}"
        )


@router.get("/{company_id}", response_model=CompanyResponse)
async def get_company(
    company_id: str,
    db: AsyncSession = Depends(get_db),
    admin: Admin = Depends(get_current_admin)
):
    """Get company by ID"""
    company = await tenant_service.get_company_by_id(db, company_id)
    if not company:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Company not found"
        )
    
    return CompanyResponse(
        company_id=company.company_id,
        name=company.name,
        email=company.email,
        n8n_credential_id=company.n8n_credential_id,
        status=company.status,
        created_at=company.created_at,
        has_oauth_connected=company.encrypted_access_token is not None
    )

