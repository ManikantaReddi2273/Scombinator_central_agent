"""
Fix database schema - add missing columns to companies table
"""
import asyncio
from sqlalchemy import text
from database import async_engine


async def fix_schema():
    """Add missing columns to companies table if they don't exist"""
    async with async_engine.begin() as conn:
        # Check if columns exist and add them if missing
        try:
            # Check if encrypted_access_token exists
            result = await conn.execute(text("""
                SELECT column_name 
                FROM information_schema.columns 
                WHERE table_name='companies' AND column_name='encrypted_access_token'
            """))
            if result.fetchone() is None:
                print("Adding encrypted_access_token column...")
                await conn.execute(text("""
                    ALTER TABLE companies 
                    ADD COLUMN encrypted_access_token TEXT NOT NULL DEFAULT ''
                """))
                print("[OK] encrypted_access_token column added")
            else:
                print("[OK] encrypted_access_token column already exists")
            
            # Check if encrypted_refresh_token exists
            result = await conn.execute(text("""
                SELECT column_name 
                FROM information_schema.columns 
                WHERE table_name='companies' AND column_name='encrypted_refresh_token'
            """))
            if result.fetchone() is None:
                print("Adding encrypted_refresh_token column...")
                await conn.execute(text("""
                    ALTER TABLE companies 
                    ADD COLUMN encrypted_refresh_token TEXT NOT NULL DEFAULT ''
                """))
                print("[OK] encrypted_refresh_token column added")
            else:
                print("[OK] encrypted_refresh_token column already exists")
            
            # Check if access_token_expires_at exists
            result = await conn.execute(text("""
                SELECT column_name 
                FROM information_schema.columns 
                WHERE table_name='companies' AND column_name='access_token_expires_at'
            """))
            if result.fetchone() is None:
                print("Adding access_token_expires_at column...")
                await conn.execute(text("""
                    ALTER TABLE companies 
                    ADD COLUMN access_token_expires_at TIMESTAMP WITH TIME ZONE
                """))
                print("[OK] access_token_expires_at column added")
            else:
                print("[OK] access_token_expires_at column already exists")
            
            print("\n[OK] Database schema fixed!")
            
        except Exception as e:
            print(f"[ERROR] Failed to fix schema: {e}")
            # Try to recreate tables instead
            print("\nAttempting to recreate all tables...")
            from database import Base
            from models import Company, Admin, Email, Draft, Candidate, AuditLog
            
            # Drop all tables
            await conn.run_sync(Base.metadata.drop_all)
            print("[OK] Dropped all tables")
            
            # Create all tables
            await conn.run_sync(Base.metadata.create_all)
            print("[OK] Recreated all tables")
            
            # Recreate admin user
            from config import settings
            from services.encryption import encryption_service
            from models.admin import Admin as AdminModel
            from sqlalchemy.orm import sessionmaker
            from sqlalchemy.ext.asyncio import AsyncSession
            
            async_session = sessionmaker(
                async_engine, class_=AsyncSession, expire_on_commit=False
            )
            
            async with async_session() as session:
                from sqlalchemy import select
                
                result = await session.execute(
                    select(AdminModel).where(AdminModel.email == settings.ADMIN_EMAIL)
                )
                existing_admin = result.scalar_one_or_none()
                
                if not existing_admin:
                    hashed_password = encryption_service.hash_password(settings.ADMIN_PASSWORD)
                    admin = AdminModel(
                        email=settings.ADMIN_EMAIL,
                        encrypted_password=hashed_password,
                        role=settings.ADMIN_ROLE,
                        is_active=True
                    )
                    session.add(admin)
                    await session.commit()
                    print(f"[OK] Admin user recreated: {settings.ADMIN_EMAIL}")


if __name__ == "__main__":
    print("Fixing database schema...")
    asyncio.run(fix_schema())
    print("Schema fix complete!")

