"""
Company management routes
"""
from fastapi import APIRouter, Depends, HTTPException, status, Query, Request
from fastapi.responses import RedirectResponse
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from typing import Optional
from database import get_db
from models.admin import Admin
from models.company import Company
from schemas.company import CompanyRegisterRequest, CompanyResponse, CompanyCreate, OAuthConnectRequest
from services.tenant import tenant_service
from services.audit_logger import audit_logger_service
from auth.jwt import get_current_admin
from config import settings
import httpx
import traceback
import logging

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/api/companies", tags=["Companies"])


def _frontend_redirect(path: str = "/companies", query: str = "") -> RedirectResponse:
    """Redirect browser back to the React dashboard after OAuth."""
    base = (settings.FRONTEND_URL or "http://localhost:3000").rstrip("/")
    url = f"{base}{path}"
    if query:
        url = f"{url}?{query}"
    return RedirectResponse(url=url, status_code=302)


def _oauth_callback_redirect_uri(request: Request) -> str:
    """Public callback URL Google redirects to (must match Google Cloud Console)."""
    # Prefer configured backend public URL if set via Render
    configured = (getattr(settings, "BACKEND_PUBLIC_URL", None) or "").strip().rstrip("/")
    if configured:
        return f"{configured}/api/companies/oauth/callback"
    # Fallback: derive from the incoming request (works on Render)
    return str(request.url_for("google_oauth_callback"))


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
    Connect or update OAuth tokens for an existing company (Step 2)
    This endpoint is called by n8n after OAuth flow completes.
    Can be used to connect new tokens or update existing ones (e.g., to add new scopes).
    No admin auth required - n8n calls this directly.
    """
    # Check if company exists
    company = await tenant_service.get_company_by_id(db, company_id)
    if not company:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Company with id {company_id} not found"
        )
    
    # Allow updating existing tokens (for re-authentication with new scopes)
    is_update = company.encrypted_access_token is not None
    if is_update:
        logger.info(f"Updating OAuth tokens for company {company_id} (re-authentication)")
    
    # Connect or update OAuth tokens
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


@router.get("/oauth/callback", name="google_oauth_callback")
async def google_oauth_callback(
    request: Request,
    db: AsyncSession = Depends(get_db),
    code: Optional[str] = Query(None),
    state: Optional[str] = Query(None),
    error: Optional[str] = Query(None),
    error_description: Optional[str] = Query(None),
):
    """
    Google OAuth redirect target for production (Render).
    Exchanges the authorization code for tokens and stores them on the company.
    Does not require n8n — works when n8n stays on local Docker.
    """
    if error:
        logger.error("Google OAuth error: %s — %s", error, error_description)
        return _frontend_redirect("/companies", f"oauth=error&message={error}")

    if not code or not state:
        return _frontend_redirect("/companies", "oauth=error&message=missing_code_or_state")

    client_id = (settings.GOOGLE_CLIENT_ID or "").strip()
    client_secret = (settings.GOOGLE_CLIENT_SECRET or "").strip()
    if not client_id or not client_secret:
        logger.error("GOOGLE_CLIENT_ID / GOOGLE_CLIENT_SECRET not configured on backend")
        return _frontend_redirect("/companies", "oauth=error&message=server_oauth_not_configured")

    redirect_uri = _oauth_callback_redirect_uri(request)
    company_id = state.strip()

    try:
        async with httpx.AsyncClient(timeout=30.0) as client:
            token_resp = await client.post(
                "https://oauth2.googleapis.com/token",
                data={
                    "code": code,
                    "client_id": client_id,
                    "client_secret": client_secret,
                    "redirect_uri": redirect_uri,
                    "grant_type": "authorization_code",
                },
                headers={"Content-Type": "application/x-www-form-urlencoded"},
            )
        if token_resp.status_code != 200:
            logger.error("Google token exchange failed: %s %s", token_resp.status_code, token_resp.text)
            return _frontend_redirect("/companies", "oauth=error&message=token_exchange_failed")

        token_data = token_resp.json()
        access_token = token_data.get("access_token")
        refresh_token = token_data.get("refresh_token")
        expires_in = int(token_data.get("expires_in") or 3600)

        if not access_token:
            return _frontend_redirect("/companies", "oauth=error&message=no_access_token")

        # Google may omit refresh_token on re-consent; keep existing if missing
        if not refresh_token:
            company = await tenant_service.get_company_by_id(db, company_id)
            if company and company.encrypted_refresh_token:
                from services.encryption import encryption_service
                refresh_token = encryption_service.decrypt(company.encrypted_refresh_token)
            else:
                return _frontend_redirect("/companies", "oauth=error&message=no_refresh_token")

        await tenant_service.connect_oauth_to_company(
            db=db,
            company_id=company_id,
            access_token=access_token,
            refresh_token=refresh_token,
            n8n_credential_id=None,
            expires_in=expires_in,
        )
        logger.info("OAuth connected for company %s via backend callback", company_id)
        return _frontend_redirect("/companies", "oauth=success")
    except Exception as e:
        logger.error("OAuth callback failed: %s", str(e), exc_info=True)
        return _frontend_redirect("/companies", "oauth=error&message=callback_failed")


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


@router.get("/{company_id}/oauth-scopes")
async def check_oauth_scopes(
    company_id: str,
    db: AsyncSession = Depends(get_db),
    admin: Admin = Depends(get_current_admin)
):
    """
    Check what OAuth scopes are available for a company's tokens
    Useful for debugging scope issues
    """
    from services.token_manager import token_manager_service
    import httpx
    
    try:
        company = await tenant_service.get_company_by_id(db, company_id)
        if not company:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Company not found"
            )
        
        if not company.encrypted_access_token:
            return {
                "company_id": company_id,
                "has_oauth": False,
                "message": "OAuth not connected"
            }
        
        # Get valid token
        access_token = await token_manager_service.get_valid_token(db, company_id)
        
        # Use tokeninfo endpoint to check scopes
        import requests
        response = requests.get(
            f"https://www.googleapis.com/oauth2/v1/tokeninfo?access_token={access_token}",
            timeout=10
        )
        if response.status_code == 200:
            token_info = response.json()
            scopes = token_info.get("scope", "").split()
            return {
                "company_id": company_id,
                "company_name": company.name,
                "has_oauth": True,
                "scopes": scopes,
                "has_sheets_scope": "https://www.googleapis.com/auth/spreadsheets" in scopes,
                "has_gmail_scope": "https://www.googleapis.com/auth/gmail.modify" in scopes,
                "has_drive_scope": any("drive" in s for s in scopes),
                "expires_in": token_info.get("expires_in"),
                "audience": token_info.get("audience")
            }
        else:
            return {
                "company_id": company_id,
                "has_oauth": True,
                "error": "Could not verify token scopes",
                "status_code": response.status_code
            }
    except Exception as e:
        logger.error(f"Error checking OAuth scopes: {str(e)}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error checking scopes: {str(e)}"
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

