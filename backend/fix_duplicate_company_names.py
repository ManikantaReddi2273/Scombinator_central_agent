"""
Script to fix duplicate company names by renaming them
This adds a suffix to duplicate names to make them unique.
"""
import asyncio
from sqlalchemy import text
from database import async_engine


async def fix_duplicate_names():
    """Rename duplicate company names by adding a suffix"""
    async with async_engine.begin() as conn:
        try:
            # Find duplicate names
            result = await conn.execute(text("""
                SELECT name, COUNT(*) as count
                FROM companies
                GROUP BY name
                HAVING COUNT(*) > 1
            """))
            duplicates = result.fetchall()
            
            if not duplicates:
                print("[OK] No duplicate company names found!")
                return
            
            print(f"[INFO] Found {len(duplicates)} duplicate name(s):")
            for row in duplicates:
                print(f"  - '{row[0]}' appears {row[1]} times")
            
            print("\n[INFO] Renaming duplicates...")
            
            for row in duplicates:
                name = row[0]
                # Get all companies with this name
                result = await conn.execute(text("""
                    SELECT company_id, name, email 
                    FROM companies 
                    WHERE name = :name
                    ORDER BY created_at ASC
                """), {"name": name})
                companies = result.fetchall()
                
                # Keep the first one, rename the rest
                for idx, company in enumerate(companies):
                    if idx == 0:
                        print(f"  [KEEP] ID: {company[0]}, Name: {company[1]}, Email: {company[2]}")
                    else:
                        new_name = f"{name} ({idx + 1})"
                        await conn.execute(text("""
                            UPDATE companies 
                            SET name = :new_name 
                            WHERE company_id = :company_id
                        """), {"new_name": new_name, "company_id": company[0]})
                        print(f"  [RENAMED] ID: {company[0]}, Old: {company[1]}, New: {new_name}, Email: {company[2]}")
            
            print("\n[OK] Duplicate names fixed!")
            
        except Exception as e:
            print(f"[ERROR] Failed to fix duplicates: {e}")
            raise


if __name__ == "__main__":
    print("Fixing duplicate company names...")
    asyncio.run(fix_duplicate_names())
    print("Done! Now you can run migrate_add_unique_name_constraint.py")

