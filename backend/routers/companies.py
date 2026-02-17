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
import logging

logger = logging.getLogger(__name__)

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


@router.post("/{company_id}/refresh-brand-context")
async def refresh_brand_context(
    company_id: str,
    db: AsyncSession = Depends(get_db),
    admin: Admin = Depends(get_current_admin)
):
    """
    Manually refresh brand context cache from Google Drive
    
    Forces reload of all brand context documents (COMPANY.md, VOICE.md, etc.)
    from the company's Google Drive and updates the Redis cache.
    """
    from services.brand_context_loader import brand_context_loader
    
    # Check if company exists
    company = await tenant_service.get_company_by_id(db, company_id)
    if not company:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Company with id {company_id} not found"
        )
    
    try:
        # Refresh cache (deletes old cache and reloads from Drive)
        brand_context = await brand_context_loader.refresh_cache(db, company_id)
        
        # Get list of loaded documents
        full_context = brand_context.get("full", {})
        loaded_documents = []
        for key in ["company", "voice", "playbooks", "policies", "knowledge"]:
            if full_context.get(key):
                loaded_documents.append(f"{key.upper()}.md")
        
        templates_count = len(full_context.get("templates", {}))
        if templates_count > 0:
            loaded_documents.append(f"TEMPLATES ({templates_count} files)")
        
        return {
            "status": "success",
            "message": "Brand context refreshed successfully",
            "company_id": company_id,
            "company_name": company.name,
            "loaded_documents": loaded_documents,
            "total_documents": len(loaded_documents)
        }
    except Exception as e:
        logger.error(f"Error refreshing brand context for company {company_id}: {str(e)}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error refreshing brand context: {str(e)}"
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


@router.get("/with-oauth", response_model=list[CompanyResponse])
async def get_companies_with_oauth(
    db: AsyncSession = Depends(get_db)
):
    """
    Get all companies with OAuth connected (called by n8n)
    No admin auth required - n8n calls this directly
    """
    try:
        result = await db.execute(
            select(Company)
            .where(Company.encrypted_access_token.isnot(None))
            .where(Company.status == "active")
            .order_by(Company.created_at.desc())
        )
        companies = result.scalars().all()
        
        return [
            CompanyResponse(
                company_id=c.company_id,
                name=c.name,
                email=c.email,
                n8n_credential_id=c.n8n_credential_id,
                status=c.status,
                created_at=c.created_at,
                has_oauth_connected=True
            )
            for c in companies
        ]
    except Exception as e:
        import logging
        logger = logging.getLogger(__name__)
        logger.error(f"Error fetching companies with OAuth: {str(e)}")
        logger.error(traceback.format_exc())
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error fetching companies: {str(e)}"
        )


@router.get("/{company_id}/gmail-token")
async def get_gmail_token(
    company_id: str,
    db: AsyncSession = Depends(get_db)
):
    """
    Get valid Gmail access token for company (called by n8n)
    Returns decrypted, refreshed token ready to use
    No admin auth required - n8n calls this directly
    """
    from services.token_manager import token_manager_service
    import uuid
    
    try:
        # Get valid token (automatically refreshes if expired)
        access_token = await token_manager_service.get_valid_token(db, company_id)
        
        # Get company email for reference
        result = await db.execute(
            select(Company).where(Company.company_id == uuid.UUID(company_id))
        )
        company = result.scalar_one_or_none()
        
        if not company:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Company not found"
            )
        
        return {
            "company_id": company_id,
            "company_email": company.email,
            "access_token": access_token,
            "expires_at": company.access_token_expires_at.isoformat() if company.access_token_expires_at else None
        }
    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=str(e)
        )
    except ValueError as e:
        # This is already handled above, but catch it here too for safety
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=str(e)
        )
    except Exception as e:
        import logging
        logger = logging.getLogger(__name__)
        logger.error(f"Error getting Gmail token: {str(e)}")
        logger.error(traceback.format_exc())
        # Return more detailed error in development
        error_detail = str(e)
        if settings.DEBUG:
            error_detail = f"{str(e)}\n\n{traceback.format_exc()}"
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=error_detail
        )


@router.get("/{company_id}", response_model=CompanyResponse)
async def get_company(
    company_id: str,
    db: AsyncSession = Depends(get_db)
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

