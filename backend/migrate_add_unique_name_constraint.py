"""
Migration: Add unique constraint to companies.name column
This ensures no two companies can have the same name.
"""
import asyncio
from sqlalchemy import text
from database import async_engine


async def migrate_add_unique_name_constraint():
    """Add unique constraint to companies.name column"""
    async with async_engine.begin() as conn:
        try:
            # Check if unique constraint already exists
            result = await conn.execute(text("""
                SELECT constraint_name 
                FROM information_schema.table_constraints 
                WHERE table_name='companies' 
                AND constraint_type='UNIQUE' 
                AND constraint_name LIKE '%name%'
            """))
            existing_constraint = result.fetchone()
            
            if existing_constraint:
                print(f"[OK] Unique constraint on 'name' already exists: {existing_constraint[0]}")
            else:
                # Check for duplicate names before adding constraint
                result = await conn.execute(text("""
                    SELECT name, COUNT(*) as count
                    FROM companies
                    GROUP BY name
                    HAVING COUNT(*) > 1
                """))
                duplicates = result.fetchall()
                
                if duplicates:
                    print("[WARNING] Found duplicate company names:")
                    for row in duplicates:
                        print(f"  - '{row[0]}' appears {row[1]} times")
                    print("\n[ERROR] Cannot add unique constraint while duplicates exist.")
                    print("Please rename or delete duplicate companies first.")
                    print("\nDuplicate companies:")
                    for row in duplicates:
                        result = await conn.execute(text("""
                            SELECT company_id, name, email 
                            FROM companies 
                            WHERE name = :name
                        """), {"name": row[0]})
                        companies = result.fetchall()
                        for company in companies:
                            print(f"  - ID: {company[0]}, Name: {company[1]}, Email: {company[2]}")
                    return
                
                # Add unique constraint
                print("Adding unique constraint to 'name' column...")
                await conn.execute(text("""
                    ALTER TABLE companies 
                    ADD CONSTRAINT companies_name_unique UNIQUE (name)
                """))
                print("[OK] Unique constraint added to 'name' column")
            
            print("\n[OK] Migration complete! Company names are now unique.")
            
        except Exception as e:
            print(f"[ERROR] Migration failed: {e}")
            raise


if __name__ == "__main__":
    print("Migrating companies table to add unique constraint on 'name' column...")
    asyncio.run(migrate_add_unique_name_constraint())
    print("Migration complete!")

