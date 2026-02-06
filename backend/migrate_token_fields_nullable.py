"""
Migration: Make token fields nullable in companies table
This enables two-step registration where companies can exist without OAuth tokens initially.
"""
import asyncio
from sqlalchemy import text
from database import async_engine


async def migrate_token_fields_nullable():
    """Make encrypted_access_token and encrypted_refresh_token nullable"""
    async with async_engine.begin() as conn:
        try:
            # Check current NOT NULL constraint
            result = await conn.execute(text("""
                SELECT is_nullable 
                FROM information_schema.columns 
                WHERE table_name='companies' AND column_name='encrypted_access_token'
            """))
            row = result.fetchone()
            
            if row and row[0] == 'NO':
                print("Making encrypted_access_token nullable...")
                await conn.execute(text("""
                    ALTER TABLE companies 
                    ALTER COLUMN encrypted_access_token DROP NOT NULL
                """))
                print("[OK] encrypted_access_token is now nullable")
            else:
                print("[OK] encrypted_access_token is already nullable")
            
            # Check refresh token
            result = await conn.execute(text("""
                SELECT is_nullable 
                FROM information_schema.columns 
                WHERE table_name='companies' AND column_name='encrypted_refresh_token'
            """))
            row = result.fetchone()
            
            if row and row[0] == 'NO':
                print("Making encrypted_refresh_token nullable...")
                await conn.execute(text("""
                    ALTER TABLE companies 
                    ALTER COLUMN encrypted_refresh_token DROP NOT NULL
                """))
                print("[OK] encrypted_refresh_token is now nullable")
            else:
                print("[OK] encrypted_refresh_token is already nullable")
            
            # Check n8n_credential_id
            result = await conn.execute(text("""
                SELECT is_nullable 
                FROM information_schema.columns 
                WHERE table_name='companies' AND column_name='n8n_credential_id'
            """))
            row = result.fetchone()
            
            if row and row[0] == 'NO':
                print("Making n8n_credential_id nullable...")
                await conn.execute(text("""
                    ALTER TABLE companies 
                    ALTER COLUMN n8n_credential_id DROP NOT NULL
                """))
                print("[OK] n8n_credential_id is now nullable")
            else:
                print("[OK] n8n_credential_id is already nullable")
            
            print("\n[OK] Migration complete! Token fields and n8n_credential_id are now nullable.")
            
        except Exception as e:
            print(f"[ERROR] Migration failed: {e}")
            raise


if __name__ == "__main__":
    print("Migrating companies table to make token fields nullable...")
    asyncio.run(migrate_token_fields_nullable())
    print("Migration complete!")

