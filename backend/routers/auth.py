"""
Authentication routes
"""
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from database import get_db
from models.admin import Admin
from schemas.auth import LoginRequest, LoginResponse
from auth.jwt import create_access_token
from services.encryption import encryption_service

router = APIRouter(prefix="/api/auth", tags=["Authentication"])


@router.post("/login", response_model=LoginResponse)
async def login(
    login_data: LoginRequest,
    db: AsyncSession = Depends(get_db)
):
    """Admin login endpoint"""
    # Find admin by email
    result = await db.execute(
        select(Admin).where(Admin.email == login_data.email)
    )
    admin = result.scalar_one_or_none()
    
    if not admin:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Incorrect email or password"
        )
    
    # Verify password
    if not encryption_service.verify_password(login_data.password, admin.encrypted_password):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Incorrect email or password"
        )
    
    # Check if admin is active
    if not admin.is_active:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Admin account is inactive"
        )
    
    # Create access token
    access_token = create_access_token(data={"sub": admin.email, "role": admin.role})
    
    return LoginResponse(
        access_token=access_token,
        token_type="bearer",
        admin_email=admin.email,
        role=admin.role
    )

