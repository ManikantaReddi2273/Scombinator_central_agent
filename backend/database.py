"""
Database connection and session management
"""
from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession, async_sessionmaker
from sqlalchemy.orm import declarative_base
from sqlalchemy import create_engine
from config import settings

# Async engine for FastAPI
# Small pool by default — Render free Postgres rejects large connection pools and
# OOMs when many Flow 1 jobs open sessions in parallel.
async_engine = create_async_engine(
    settings.DATABASE_URL,
    echo=settings.DEBUG,
    future=True,
    pool_pre_ping=True,  # Verify connections before using
    pool_recycle=3600,   # Recycle connections after 1 hour
    pool_timeout=30,     # Timeout when getting connection from pool
    pool_size=settings.DB_POOL_SIZE,
    max_overflow=settings.DB_MAX_OVERFLOW,
    connect_args={
        "server_settings": {
            "application_name": "s_combinator_backend"
        },
        "timeout": 30,  # Connection timeout in seconds (increased)
    }
)

# Sync engine for Alembic migrations
sync_engine = create_engine(
    settings.DATABASE_URL_SYNC,
    echo=settings.DEBUG
)

# Session factories
AsyncSessionLocal = async_sessionmaker(
    async_engine,
    class_=AsyncSession,
    expire_on_commit=False,
    autocommit=False,
    autoflush=False
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
                # Check if it's a connection error
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
        # This catches errors when creating the session itself
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

