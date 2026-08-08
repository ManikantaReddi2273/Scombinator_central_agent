"""
Database connection and session management
"""
from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession, async_sessionmaker
from sqlalchemy.orm import declarative_base
from sqlalchemy import create_engine
from config import settings


def _is_neon_or_pooler(url: str) -> bool:
    u = (url or "").lower()
    return "neon.tech" in u or "pooler" in u


def _async_connect_args() -> dict:
    """
    Neon (and other PgBouncer poolers) need SSL + disabled statement cache.
    Local Postgres does not need those extras.
    """
    args: dict = {
        "timeout": 30,
        "server_settings": {
            "application_name": "s_combinator_backend",
        },
    }
    if _is_neon_or_pooler(settings.DATABASE_URL):
        # Required for Neon pooler / transaction-mode PgBouncer
        args["statement_cache_size"] = 0
        args["ssl"] = True
    return args


# Async engine for FastAPI
# Small pool by default — free Postgres / Neon free reject large connection pools.
async_engine = create_async_engine(
    settings.DATABASE_URL,
    echo=settings.DEBUG,
    future=True,
    pool_pre_ping=True,
    pool_recycle=300 if _is_neon_or_pooler(settings.DATABASE_URL) else 3600,
    pool_timeout=30,
    pool_size=settings.DB_POOL_SIZE,
    max_overflow=settings.DB_MAX_OVERFLOW,
    connect_args=_async_connect_args(),
)

# Sync engine for Alembic / sync helpers
_sync_kwargs = {"echo": settings.DEBUG}
if _is_neon_or_pooler(settings.DATABASE_URL_SYNC):
    _sync_kwargs["connect_args"] = {"sslmode": "require"}

sync_engine = create_engine(settings.DATABASE_URL_SYNC, **_sync_kwargs)

# Session factories
AsyncSessionLocal = async_sessionmaker(
    async_engine,
    class_=AsyncSession,
    expire_on_commit=False,
    autocommit=False,
    autoflush=False,
)

# Base class for models
Base = declarative_base()


# Dependency for FastAPI routes
async def get_db():
    """Get database session"""
    try:
        async with AsyncSessionLocal() as session:
            try:
                yield session
                await session.commit()
            except Exception as e:
                await session.rollback()
                error_msg = str(e).lower()
                if "connection" in error_msg or "timeout" in error_msg or "refused" in error_msg or "could not connect" in error_msg:
                    from fastapi import HTTPException, status
                    import logging
                    logger = logging.getLogger(__name__)
                    logger.error(f"Database connection error: {str(e)}")
                    raise HTTPException(
                        status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
                        detail=f"Database connection error: {str(e)}. Please check if PostgreSQL is running and DATABASE_URL is correct in .env file."
                    )
                raise
            finally:
                await session.close()
    except Exception as e:
        from fastapi import HTTPException, status
        import logging
        logger = logging.getLogger(__name__)
        logger.error(f"Failed to create database session: {str(e)}")
        error_msg = str(e).lower()
        if "connection" in error_msg or "timeout" in error_msg or "refused" in error_msg or "could not connect" in error_msg:
            raise HTTPException(
                status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
                detail=f"Database connection error: {str(e)}. Please check if PostgreSQL is running and DATABASE_URL is correct in .env file."
            )
        raise
