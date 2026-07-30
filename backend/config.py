"""
Configuration settings for S Combinator Central Agent Platform
"""
from pathlib import Path
from pydantic_settings import BaseSettings
from typing import Optional

# Load .env from backend directory so it works regardless of CWD
_BACKEND_DIR = Path(__file__).resolve().parent
_ENV_FILE = _BACKEND_DIR / ".env"


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
    # Keep small on Render free (limited Postgres connections + 512MB RAM)
    DB_POOL_SIZE: int = 5
    DB_MAX_OVERFLOW: int = 5
    
    # JWT
    JWT_SECRET_KEY: str
    JWT_ALGORITHM: str = "HS256"
    JWT_ACCESS_TOKEN_EXPIRE_MINUTES: int = 1440  # 24 hours
    
    # Encryption
    ENCRYPTION_KEY: str  # 32 bytes for AES-256
    
    # Google OAuth (backend callback on Render; n8n still optional locally)
    GOOGLE_CLIENT_ID: Optional[str] = None
    GOOGLE_CLIENT_SECRET: Optional[str] = None
    # Optional explicit public backend URL, e.g. https://scombinator-backend.onrender.com
    BACKEND_PUBLIC_URL: Optional[str] = None
    
    # OpenAI
    OPENAI_API_KEY: Optional[str] = None
    OPENAI_MODEL: str = "gpt-4o"  # Use GPT-4o for best quality, can override in .env
    # Optional faster model for "Edit with AI" only (e.g. gpt-4o-mini). If set, draft edit uses this for lower latency.
    OPENAI_DRAFT_EDIT_MODEL: Optional[str] = None
    
    # Business timezone for CRM dates (LEADS, ACTIVITIES, TASKS). DB remains UTC.
    APP_TIMEZONE: str = "Asia/Kolkata"

    # n8n
    N8N_WEBHOOK_URL: str = "http://localhost:5678/webhook"
    # Optional: API key for n8n / service calls (e.g. Update CRM). If set, requests with X-API-Key: <value> are accepted.
    N8N_SERVICE_API_KEY: Optional[str] = None

    # Production frontend origin (e.g. https://scombinator-frontend.onrender.com)
    FRONTEND_URL: Optional[str] = None
    
    # Redis
    REDIS_HOST: str = "localhost"
    REDIS_PORT: int = 6379
    REDIS_DB: int = 0
    REDIS_PASSWORD: Optional[str] = None
    
    class Config:
        env_file = str(_ENV_FILE) if _ENV_FILE.exists() else ".env"
        case_sensitive = True
        extra = "ignore"  # Ignore extra fields in .env file


settings = Settings()

