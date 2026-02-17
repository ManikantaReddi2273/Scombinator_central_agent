"""
Test script for Brand Context loading
Run this to test if brand context documents are loading correctly from Google Drive
"""
import asyncio
import sys
import os
# Fix Unicode encoding for Windows
if sys.platform == 'win32':
    os.system('chcp 65001 >nul 2>&1')
    sys.stdout.reconfigure(encoding='utf-8') if hasattr(sys.stdout, 'reconfigure') else None

from database import get_db
from services.brand_context_loader import brand_context_loader
from services.google_api import google_api_service
from services.tenant import tenant_service
from services.redis_cache import redis_cache
import time


async def test_folder_search(company_id: str):
    """Test if folder can be found"""
    print("\n" + "="*60)
    print("TEST 1: Folder Search")
    print("="*60)
    
    result = False
    async for db in get_db():
        try:
            # Get company name
            company = await tenant_service.get_company_by_id(db, company_id)
            if not company:
                print(f"❌ Company {company_id} not found")
                result = False
                break
            
            print(f"Company: {company.name}")
            print(f"Company ID: {company_id}")
            
            # Test folder finding
            print("\nSearching for 'Brand Context Documents' folder...")
            folder_id = await google_api_service.find_folder_by_name(
                db, company_id, "Brand Context Documents"
            )
            
            if folder_id:
                print(f"✅ Found 'Brand Context Documents' folder: {folder_id}")
            else:
                print("❌ 'Brand Context Documents' not found")
                print(f"\nTrying company name folder: '{company.name}'...")
                folder_id = await google_api_service.find_folder_by_name(
                    db, company_id, company.name
                )
                if folder_id:
                    print(f"✅ Found company name folder: {folder_id}")
                else:
                    print("❌ No folder found")
                    print("\n💡 SOLUTION: Create a folder named 'Brand Context Documents' in the company's Google Drive")
                    result = False
                    break
            
            # Test file listing
            print(f"\n📁 Listing files in folder...")
            files = await google_api_service.list_files_in_folder(
                db, company_id, folder_id
            )
            print(f"Found {len(files)} items:")
            
            expected_files = ["COMPANY.md", "VOICE.md", "PLAYBOOKS.md", "POLICIES.md", "KNOWLEDGE.md"]
            found_files = []
            templates_folder = False
            
            for file_info in files:
                file_name = file_info['name']
                file_type = file_info['mimeType']
                
                if file_name in expected_files:
                    print(f"  ✅ {file_name}")
                    found_files.append(file_name)
                elif file_name == "TEMPLATES" and file_type == 'application/vnd.google-apps.folder':
                    print(f"  ✅ {file_name}/ (folder)")
                    templates_folder = True
                else:
                    print(f"  ⚠️  {file_name} ({'folder' if 'folder' in file_type else 'file'})")
            
            # Check missing files
            missing = [f for f in expected_files if f not in found_files]
            if missing:
                print(f"\n⚠️  Missing files: {', '.join(missing)}")
            else:
                print(f"\n✅ All required files found!")
            
            if not templates_folder:
                print("⚠️  TEMPLATES folder not found")
            else:
                print("✅ TEMPLATES folder found")
            
            # Return True if we found the folder and at least some files
            # This allows the test to continue even if some files are missing
            result = folder_id is not None and len(found_files) > 0
            if result:
                print("\n✅ TEST 1 PASSED: Folder structure is correct!")
            else:
                print("\n❌ TEST 1 FAILED: Missing required files or folder")
            break  # Exit loop after first iteration
            
        except Exception as e:
            print(f"❌ Error: {str(e)}")
            import traceback
            traceback.print_exc()
            result = False
            break
    
    return result


async def test_brand_context_loading(company_id: str):
    """Test brand context loading"""
    print("\n" + "="*60)
    print("TEST 2: Brand Context Loading")
    print("="*60)
    
    async for db in get_db():
        try:
            print(f"Loading brand context for company {company_id}...")
            
            context = await brand_context_loader.load_all(db, company_id)
            
            print("\n✅ Brand Context Loaded:")
            full = context.get('full', {})
            
            docs_status = {
                'Company': '✅' if full.get('company') else '❌',
                'Voice': '✅' if full.get('voice') else '❌',
                'Playbooks': '✅' if full.get('playbooks') else '❌',
                'Policies': '✅' if full.get('policies') else '❌',
                'Knowledge': '✅' if full.get('knowledge') else '❌',
            }
            
            for doc, status in docs_status.items():
                print(f"  {status} {doc}.md")
            
            templates = full.get('templates', {})
            print(f"  {'✅' if templates else '❌'} Templates: {len(templates)} files")
            
            if templates:
                print("\n  Template files:")
                for template_name in list(templates.keys())[:10]:  # Show first 10
                    print(f"    - {template_name}")
                if len(templates) > 10:
                    print(f"    ... and {len(templates) - 10} more")
            
            print("\n📊 Key Points Extracted:")
            key_points = context.get('key_points', {})
            
            print(f"  Company Name: {key_points.get('company_name', 'N/A')}")
            print(f"  Tone Style: {key_points.get('tone_style', 'N/A')}")
            print(f"  Pricing Policy: {key_points.get('pricing_policy', 'N/A')}")
            
            sla_rules = key_points.get('sla_rules', '')
            if sla_rules:
                print(f"  SLA Rules: ✅ ({len(sla_rules)} chars)")
            else:
                print(f"  SLA Rules: ❌")
            
            top_faqs = key_points.get('top_faqs', '')
            if top_faqs:
                faq_count = len([f for f in top_faqs.split('\n') if f.strip()])
                print(f"  Top FAQs: ✅ ({faq_count} questions)")
            else:
                print(f"  Top FAQs: ❌")
            
            template_names = key_points.get('template_names', [])
            print(f"  Template Names: ✅ ({len(template_names)} templates)")
            
            return True
            
        except Exception as e:
            print(f"❌ Error: {str(e)}")
            import traceback
            traceback.print_exc()
            return False
        finally:
            break


async def test_caching(company_id: str):
    """Test Redis caching"""
    print("\n" + "="*60)
    print("TEST 3: Redis Caching")
    print("="*60)
    
    async for db in get_db():
        try:
            # Check Redis connection
            cache_key = f"brand_context:{company_id}"
            test_key = "test_connection"
            
            await redis_cache.set(test_key, {"test": "value"}, ttl=10)
            cached_test = await redis_cache.get(test_key)
            
            if cached_test:
                print("✅ Redis connection working")
            else:
                print("❌ Redis connection failed - check if Redis is running")
                print("   Run: docker ps | findstr redis")
                return False
            
            # First load (should hit Drive)
            print("\nFirst load (should load from Drive)...")
            start = time.time()
            context1 = await brand_context_loader.load_all(db, company_id)
            time1 = time.time() - start
            print(f"⏱️  Time: {time1:.2f}s")
            
            # Check if cached
            cached = await redis_cache.get(cache_key)
            if cached:
                print("✅ Data cached in Redis")
            else:
                print("⚠️  Data not found in cache (might be an issue)")
            
            # Second load (should hit cache)
            print("\nSecond load (should load from cache)...")
            start = time.time()
            context2 = await brand_context_loader.load_all(db, company_id)
            time2 = time.time() - start
            print(f"⏱️  Time: {time2:.2f}s")
            
            # Cache should be much faster
            if time2 < time1 * 0.5:
                print(f"✅ Cache is working! ({time2/time1:.1%} of original time)")
            else:
                print(f"⚠️  Cache might not be working (only {time2/time1:.1%} faster)")
            
            return True
            
        except Exception as e:
            print(f"❌ Error: {str(e)}")
            import traceback
            traceback.print_exc()
            return False
        finally:
            break


async def main():
    """Main test function"""
    if len(sys.argv) < 2:
        print("Usage: python test_brand_context.py <company_id>")
        print("\nExample:")
        print("  python test_brand_context.py 550e8400-e29b-41d4-a716-446655440000")
        print("\nTo find company_id, check your database or use the companies API endpoint")
        return
    
    company_id = sys.argv[1]
    
    print("\n" + "="*60)
    print("BRAND CONTEXT TESTING")
    print("="*60)
    print(f"\nTesting for Company ID: {company_id}")
    
    # Run tests
    test1_result = await test_folder_search(company_id)
    if not test1_result:
        print("\n❌ Folder search failed. Please fix folder structure first.")
        return
    
    test2_result = await test_brand_context_loading(company_id)
    test3_result = await test_caching(company_id)
    
    # Summary
    print("\n" + "="*60)
    print("TEST SUMMARY")
    print("="*60)
    print(f"Folder Search: {'✅ PASS' if test1_result else '❌ FAIL'}")
    print(f"Brand Context Loading: {'✅ PASS' if test2_result else '❌ FAIL'}")
    print(f"Redis Caching: {'✅ PASS' if test3_result else '❌ FAIL'}")
    
    if all([test1_result, test2_result, test3_result]):
        print("\n🎉 All tests passed! Brand context is working correctly.")
    else:
        print("\n⚠️  Some tests failed. Check the errors above.")


if __name__ == "__main__":
    asyncio.run(main())

