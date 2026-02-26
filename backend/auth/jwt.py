"""
JWT authentication utilities
"""
from datetime import datetime, timedelta
from typing import Optional
from jose import JWTError, jwt
from fastapi import Depends, HTTPException, status, Request
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials, APIKeyHeader
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from config import settings
from database import get_db
from models.admin import Admin
from services.encryption import encryption_service

security = HTTPBearer()
security_optional = HTTPBearer(auto_error=False)
api_key_header = APIKeyHeader(name="X-API-Key", auto_error=False)


def create_access_token(data: dict, expires_delta: Optional[timedelta] = None) -> str:
    """Create JWT access token"""
    to_encode = data.copy()
    if expires_delta:
        expire = datetime.utcnow() + expires_delta
    else:
        expire = datetime.utcnow() + timedelta(minutes=settings.JWT_ACCESS_TOKEN_EXPIRE_MINUTES)
    
    to_encode.update({"exp": expire})
    encoded_jwt = jwt.encode(
        to_encode,
        settings.JWT_SECRET_KEY,
        algorithm=settings.JWT_ALGORITHM
    )
    return encoded_jwt


def verify_token(token: str) -> dict:
    """Verify and decode JWT token"""
    try:
        payload = jwt.decode(
            token,
            settings.JWT_SECRET_KEY,
            algorithms=[settings.JWT_ALGORITHM]
        )
        return payload
    except JWTError:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Could not validate credentials",
            headers={"WWW-Authenticate": "Bearer"},
        )


async def get_current_admin(
    credentials: HTTPAuthorizationCredentials = Depends(security),
    db: AsyncSession = Depends(get_db)
) -> Admin:
    """Get current authenticated admin"""
    try:
        token = credentials.credentials
        payload = verify_token(token)
        
        email: str = payload.get("sub")
        if email is None:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Could not validate credentials",
                headers={"WWW-Authenticate": "Bearer"},
            )
        
        result = await db.execute(
            select(Admin).where(Admin.email == email)
        )
        admin = result.scalar_one_or_none()
        
        if admin is None:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Admin not found",
                headers={"WWW-Authenticate": "Bearer"},
            )
        
        if not admin.is_active:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Admin account is inactive"
            )
        
        return admin
    except HTTPException:
        # Re-raise HTTP exceptions as-is
        raise
    except Exception as e:
        # Log and convert other exceptions to 500
        import logging
        logger = logging.getLogger(__name__)
        logger.error(f"Error in get_current_admin: {str(e)}")
        import traceback
        logger.error(traceback.format_exc())
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Authentication error: {str(e)}"
        )


# Dependency for routes
get_current_admin_dependency = Depends(get_current_admin)


def _get_api_key_from_request(request: Request) -> Optional[str]:
    """Get API key from X-API-Key header or api_key query param (for n8n)."""
    value = request.headers.get("x-api-key") or request.headers.get("X-API-Key")
    if value:
        return value.strip()
    # Fallback: query param (n8n may send key in URL when header is not available)
    q = request.query_params.get("api_key")
    return q.strip() if q else None


async def get_current_admin_or_n8n_key(
    request: Request,
    credentials: Optional[HTTPAuthorizationCredentials] = Depends(security_optional),
    api_key: Optional[str] = Depends(api_key_header),
    db: AsyncSession = Depends(get_db),
) -> Optional[Admin]:
    """
    Accept either (1) valid admin JWT Bearer token or (2) API key via X-API-Key header or api_key query param.
    Used by endpoints called by n8n (e.g. Update CRM). Returns Admin if JWT valid, None if API key valid.
    """
    sent_key = (api_key and api_key.strip()) or _get_api_key_from_request(request)
    expected_key = (settings.N8N_SERVICE_API_KEY or "").strip()

    if expected_key and sent_key and sent_key == expected_key:
        return None
    if credentials and credentials.credentials:
        try:
            return await get_current_admin(credentials, db)
        except HTTPException:
            pass
    if expected_key and credentials and credentials.credentials:
        if credentials.credentials.strip() == expected_key:
            return None

    import logging
    logger = logging.getLogger(__name__)
    logger.info(
        "Update CRM auth failed: key_sent=%s, backend_key_set=%s (check N8N_SERVICE_API_KEY in backend .env and n8n .env)",
        bool(sent_key),
        bool(expected_key),
    )
    raise HTTPException(
        status_code=status.HTTP_403_FORBIDDEN,
        detail="Not authenticated",
    )

