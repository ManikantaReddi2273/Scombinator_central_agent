"""
Migration: Add outbound email fields to emails table and drive_folder_id to companies table
This enables Flow 2 (B2B Outbound Email) functionality.
"""
import asyncio
from sqlalchemy import text
from database import async_engine


async def migrate_add_outbound_fields():
    """Add outbound fields to emails table and drive_folder_id to companies table"""
    async with async_engine.begin() as conn:
        try:
            # Check if email_type column exists
            result = await conn.execute(text("""
                SELECT column_name 
                FROM information_schema.columns 
                WHERE table_name='emails' AND column_name='email_type'
            """))
            row = result.fetchone()
            
            if not row:
                print("Adding email_type column to emails table...")
                await conn.execute(text("""
                    ALTER TABLE emails 
                    ADD COLUMN email_type VARCHAR(20) DEFAULT 'inbound'
                """))
                # Set default for existing records
                await conn.execute(text("""
                    UPDATE emails 
                    SET email_type = 'inbound' 
                    WHERE email_type IS NULL
                """))
                # Create index
                await conn.execute(text("""
                    CREATE INDEX IF NOT EXISTS ix_emails_email_type ON emails(email_type)
                """))
                print("[OK] email_type column added")
            else:
                print("[OK] email_type column already exists")
            
            # Add outbound_intent column
            result = await conn.execute(text("""
                SELECT column_name 
                FROM information_schema.columns 
                WHERE table_name='emails' AND column_name='outbound_intent'
            """))
            row = result.fetchone()
            
            if not row:
                print("Adding outbound_intent column to emails table...")
                await conn.execute(text("""
                    ALTER TABLE emails 
                    ADD COLUMN outbound_intent VARCHAR(100)
                """))
                print("[OK] outbound_intent column added")
            else:
                print("[OK] outbound_intent column already exists")
            
            # Add outbound_sequence_step column
            result = await conn.execute(text("""
                SELECT column_name 
                FROM information_schema.columns 
                WHERE table_name='emails' AND column_name='outbound_sequence_step'
            """))
            row = result.fetchone()
            
            if not row:
                print("Adding outbound_sequence_step column to emails table...")
                await conn.execute(text("""
                    ALTER TABLE emails 
                    ADD COLUMN outbound_sequence_step VARCHAR(10)
                """))
                print("[OK] outbound_sequence_step column added")
            else:
                print("[OK] outbound_sequence_step column already exists")
            
            # Add recipient_context column
            result = await conn.execute(text("""
                SELECT column_name 
                FROM information_schema.columns 
                WHERE table_name='emails' AND column_name='recipient_context'
            """))
            row = result.fetchone()
            
            if not row:
                print("Adding recipient_context column to emails table...")
                await conn.execute(text("""
                    ALTER TABLE emails 
                    ADD COLUMN recipient_context JSONB
                """))
                print("[OK] recipient_context column added")
            else:
                print("[OK] recipient_context column already exists")
            
            # Add scheduled_send_at column
            result = await conn.execute(text("""
                SELECT column_name 
                FROM information_schema.columns 
                WHERE table_name='emails' AND column_name='scheduled_send_at'
            """))
            row = result.fetchone()
            
            if not row:
                print("Adding scheduled_send_at column to emails table...")
                await conn.execute(text("""
                    ALTER TABLE emails 
                    ADD COLUMN scheduled_send_at TIMESTAMP WITH TIME ZONE
                """))
                print("[OK] scheduled_send_at column added")
            else:
                print("[OK] scheduled_send_at column already exists")
            
            # Add trigger_type column
            result = await conn.execute(text("""
                SELECT column_name 
                FROM information_schema.columns 
                WHERE table_name='emails' AND column_name='trigger_type'
            """))
            row = result.fetchone()
            
            if not row:
                print("Adding trigger_type column to emails table...")
                await conn.execute(text("""
                    ALTER TABLE emails 
                    ADD COLUMN trigger_type VARCHAR(50)
                """))
                print("[OK] trigger_type column added")
            else:
                print("[OK] trigger_type column already exists")
            
            # Add drive_folder_id to companies table
            result = await conn.execute(text("""
                SELECT column_name 
                FROM information_schema.columns 
                WHERE table_name='companies' AND column_name='drive_folder_id'
            """))
            row = result.fetchone()
            
            if not row:
                print("Adding drive_folder_id column to companies table...")
                await conn.execute(text("""
                    ALTER TABLE companies 
                    ADD COLUMN drive_folder_id VARCHAR(255)
                """))
                print("[OK] drive_folder_id column added")
            else:
                print("[OK] drive_folder_id column already exists")
            
            print("\n[OK] Migration complete! Outbound fields added to emails table and drive_folder_id added to companies table.")
            
        except Exception as e:
            print(f"[ERROR] Migration failed: {e}")
            raise


if __name__ == "__main__":
    print("Migrating database to add outbound email fields...")
    asyncio.run(migrate_add_outbound_fields())
    print("Migration complete!")

