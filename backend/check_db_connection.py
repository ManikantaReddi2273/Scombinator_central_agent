"""
Script to check database connection
Run this to verify PostgreSQL is accessible
"""
import asyncio
from database import async_engine
from sqlalchemy import text
import sys

async def check_connection():
    """Check if database connection works"""
    try:
        print("Attempting to connect to database...")
        async with async_engine.begin() as conn:
            result = await conn.execute(text("SELECT 1"))
            row = result.fetchone()
            if row:
                print("[SUCCESS] Database connection successful!")
                print(f"   Connection test returned: {row[0]}")
                
                # Try to get database name
                result = await conn.execute(text("SELECT current_database()"))
                db_name = result.fetchone()[0]
                print(f"   Connected to database: {db_name}")
                
                # Check if tables exist
                result = await conn.execute(text("""
                    SELECT table_name 
                    FROM information_schema.tables 
                    WHERE table_schema = 'public'
                    ORDER BY table_name
                """))
                tables = [row[0] for row in result.fetchall()]
                if tables:
                    print(f"   Found {len(tables)} tables: {', '.join(tables[:5])}{'...' if len(tables) > 5 else ''}")
                else:
                    print("   [WARNING] No tables found. Run 'python init_db.py' to initialize database.")
                
                return True
    except Exception as e:
        print(f"[ERROR] Database connection failed!")
        print(f"   Error: {str(e)}")
        print("\nTroubleshooting steps:")
        print("1. Check if PostgreSQL is running:")
        print("   - Windows: Check Services (services.msc) for 'postgresql'")
        print("   - Linux/Mac: Run 'sudo systemctl status postgresql' or 'brew services list'")
        print("2. Verify DATABASE_URL in .env file:")
        print("   - Format: postgresql+asyncpg://user:password@host:port/database")
        print("   - Example: postgresql+asyncpg://postgres:password@localhost:5432/s_combinator")
        print("3. Check if database exists:")
        print("   - Connect to PostgreSQL: psql -U postgres")
        print("   - Run: CREATE DATABASE s_combinator;")
        print("4. Check firewall/network settings if using remote database")
        return False

if __name__ == "__main__":
    success = asyncio.run(check_connection())
    sys.exit(0 if success else 1)
