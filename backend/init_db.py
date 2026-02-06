"""
Initialize database and create admin user
"""
import asyncio
from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession
from sqlalchemy.orm import sessionmaker
from database import Base, async_engine
from models import Admin, Company, Email, Draft, Candidate, AuditLog
from config import settings
from services.encryption import encryption_service


async def init_database():
    """Initialize database tables and create admin user"""
    # Create all tables
    async with async_engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
    
    print("Database tables created")
    
    # Create admin user
    async_session = sessionmaker(
        async_engine, class_=AsyncSession, expire_on_commit=False
    )
    
    async with async_session() as session:
        from sqlalchemy import select
        
        # Check if admin already exists
        result = await session.execute(
            select(Admin).where(Admin.email == settings.ADMIN_EMAIL)
        )
        existing_admin = result.scalar_one_or_none()
        
        if existing_admin:
            print(f"[OK] Admin user already exists: {settings.ADMIN_EMAIL}")
        else:
            # Hash password
            hashed_password = encryption_service.hash_password(settings.ADMIN_PASSWORD)
            
            # Create admin
            admin = Admin(
                email=settings.ADMIN_EMAIL,
                encrypted_password=hashed_password,
                role=settings.ADMIN_ROLE,
                is_active=True
            )
            
            session.add(admin)
            await session.commit()
            print(f"[OK] Admin user created: {settings.ADMIN_EMAIL}")
            print(f"   Password: {settings.ADMIN_PASSWORD} (encrypted in database)")


if __name__ == "__main__":
    print("Initializing database...")
    asyncio.run(init_database())
    print("Database initialization complete!")

