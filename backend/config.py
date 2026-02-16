"""
Configuration settings for S Combinator Central Agent Platform
"""
from pydantic_settings import BaseSettings
from typing import Optional


class Settings(BaseSettings):
    """Application settings loaded from environment variables"""
    
    # App Info
    APP_NAME: str = "S Combinator Central Agent Platform"
    APP_VERSION: str = "1.0.0"
    DEBUG: bool = True
    
    # Admin Credentials (initial, will be encrypted in DB)
    ADMIN_EMAIL: str
    ADMIN_PASSWORD: str
    ADMIN_ROLE: str = "ADMIN"
    
    # Database
    DATABASE_URL: str
    DATABASE_URL_SYNC: str
    LANGRAPH_CHECKPOINT_DB_URL: str
    
    # JWT
    JWT_SECRET_KEY: str
    JWT_ALGORITHM: str = "HS256"
    JWT_ACCESS_TOKEN_EXPIRE_MINUTES: int = 1440  # 24 hours
    
    # Encryption
    ENCRYPTION_KEY: str  # 32 bytes for AES-256
    
    # Google OAuth (reference only, actual OAuth via n8n)
    GOOGLE_CLIENT_ID: Optional[str] = None
    GOOGLE_CLIENT_SECRET: Optional[str] = None
    
    # OpenAI
    OPENAI_API_KEY: Optional[str] = None
    OPENAI_MODEL: str = "gpt-4o"  # Use GPT-4o for best quality, can override in .env
    
    # n8n
    N8N_WEBHOOK_URL: str = "http://localhost:5678/webhook"
    
    class Config:
        env_file = ".env"  # Read from .env file only
        case_sensitive = True
        extra = "ignore"  # Ignore extra fields in .env file


settings = Settings()

