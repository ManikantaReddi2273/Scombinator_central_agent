"""
Quick script to check database connection
"""
import asyncio
from database import async_engine
from sqlalchemy import text

async def check_connection():
    try:
        async with async_engine.begin() as conn:
            result = await conn.execute(text("SELECT 1 as test"))
            row = result.fetchone()
            print("✅ Database connection successful!")
            print(f"   Test query result: {row[0]}")
            return True
    except Exception as e:
        print(f"❌ Database connection failed: {str(e)}")
        print("\nTroubleshooting:")
        print("1. Check if PostgreSQL is running:")
        print("   Get-Service -Name postgresql*")
        print("2. Check if database exists:")
        print("   psql -U postgres -c '\\l' | Select-String 's_combinator'")
        print("3. Check DATABASE_URL in .env file")
        return False

if __name__ == "__main__":
    asyncio.run(check_connection())

