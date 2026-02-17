# Brand Context Documents Setup & Testing Guide

## How Folder Searching Works

### Hardcoded Folder Names

The backend searches for folders in this order:

1. **Primary folder name (hardcoded)**: `"Brand Context Documents"`
   - Location: `backend/services/google_api.py` line 309
   - This is the preferred folder name

2. **Fallback folder name**: Uses the **company name** from database
   - Location: `backend/services/google_api.py` line 313
   - If "Brand Context Documents" is not found, it tries the company name

### Hardcoded File Names

The backend looks for these **exact file names** (case-sensitive):

1. `COMPANY.md` - Company information
2. `VOICE.md` - Brand tone and writing style
3. `PLAYBOOKS.md` - Standard operating procedures
4. `POLICIES.md` - Rules and SLAs
5. `KNOWLEDGE.md` - FAQs and approved answers
6. `TEMPLATES/` - Folder containing email templates

**Location**: `backend/services/google_api.py` line 323

### Template Folder Structure

The backend expects:
- A `TEMPLATES` folder (exact name, case-sensitive)
- Inside TEMPLATES, it can have subfolders:
  - `outreach/` - For outreach templates
  - `hiring/` - For hiring templates
  - `responses/` - For response templates
- Templates can also be directly in TEMPLATES folder

---

## What You Need to Do

### Step 1: Create Folder Structure in Company Google Drive

For each company, you need to create this structure in their Google Drive:

```
📁 Brand Context Documents  (or use company name as folder name)
├── 📄 COMPANY.md
├── 📄 VOICE.md
├── 📄 PLAYBOOKS.md
├── 📄 POLICIES.md
├── 📄 KNOWLEDGE.md
└── 📁 TEMPLATES
    ├── 📁 outreach
    │   ├── network_outreach.md
    │   ├── warm_intro_request.md
    │   └── ...
    ├── 📁 hiring
    │   ├── interview_invite.md
    │   ├── offer_letter.md
    │   └── ...
    └── 📁 responses
        ├── new_inquiry_reply.md
        ├── pricing_inquiry.md
        └── ...
```

### Step 2: Use Your Existing Brand Context Documents

You already have a `Brand Context Documents` folder in your project! You can:

1. **Copy the structure** from your local folder to each company's Google Drive
2. **Upload the files** to Google Drive (convert to Google Docs or keep as .md files)

**Your local folder location**: 
```
S Combinator _Central Agent Platform/Brand Context Documents/
```

### Step 3: Ensure OAuth is Connected

Make sure each company has:
- OAuth tokens connected (via n8n workflow)
- Google Drive API access enabled
- Proper permissions to read files

---

## Testing Guide

### Test 1: Verify Redis Connection

```bash
# In backend directory
python test_redis.py
```

**Expected output**:
```
[SUCCESS] Redis connection successful!
[SUCCESS] Test value: Hello Redis!
```

### Test 2: Test Folder Finding (Manual API Test)

Create a test script `backend/test_brand_context.py`:

```python
import asyncio
from database import get_db
from services.google_api import google_api_service
from services.tenant import tenant_service

async def test_folder_search():
    async for db in get_db():
        # Replace with your actual company_id
        company_id = "your-company-id-here"
        
        # Get company name
        company = await tenant_service.get_company_by_id(db, company_id)
        if not company:
            print(f"Company {company_id} not found")
            return
        
        print(f"Testing for company: {company.name}")
        
        # Test folder finding
        folder_id = await google_api_service.find_folder_by_name(
            db, company_id, "Brand Context Documents"
        )
        
        if folder_id:
            print(f"✅ Found 'Brand Context Documents' folder: {folder_id}")
        else:
            print("❌ 'Brand Context Documents' not found, trying company name...")
            folder_id = await google_api_service.find_folder_by_name(
                db, company_id, company.name
            )
            if folder_id:
                print(f"✅ Found company name folder: {folder_id}")
            else:
                print("❌ No folder found")
                return
        
        # Test file listing
        files = await google_api_service.list_files_in_folder(
            db, company_id, folder_id
        )
        print(f"\n📁 Files in folder ({len(files)}):")
        for file_info in files:
            print(f"  - {file_info['name']} ({file_info['mimeType']})")
        
        break

if __name__ == "__main__":
    asyncio.run(test_folder_search())
```

**Run it**:
```bash
cd backend
python test_brand_context.py
```

### Test 3: Test Brand Context Loading

Update the test script:

```python
import asyncio
from database import get_db
from services.brand_context_loader import brand_context_loader

async def test_brand_context_loading():
    async for db in get_db():
        company_id = "your-company-id-here"
        
        print(f"Loading brand context for company {company_id}...")
        
        try:
            context = await brand_context_loader.load_all(db, company_id)
            
            print("\n✅ Brand Context Loaded:")
            print(f"  - Company: {'✅' if context['full'].get('company') else '❌'}")
            print(f"  - Voice: {'✅' if context['full'].get('voice') else '❌'}")
            print(f"  - Playbooks: {'✅' if context['full'].get('playbooks') else '❌'}")
            print(f"  - Policies: {'✅' if context['full'].get('policies') else '❌'}")
            print(f"  - Knowledge: {'✅' if context['full'].get('knowledge') else '❌'}")
            
            templates = context['full'].get('templates', {})
            print(f"  - Templates: {len(templates)} files")
            
            print("\n📊 Key Points Extracted:")
            key_points = context.get('key_points', {})
            print(f"  - Company Name: {key_points.get('company_name', 'N/A')}")
            print(f"  - Tone Style: {key_points.get('tone_style', 'N/A')}")
            print(f"  - Pricing Policy: {key_points.get('pricing_policy', 'N/A')}")
            print(f"  - SLA Rules: {'✅' if key_points.get('sla_rules') else '❌'}")
            print(f"  - Top FAQs: {len(key_points.get('top_faqs', '').split(chr(10))) if key_points.get('top_faqs') else 0}")
            
        except Exception as e:
            print(f"❌ Error: {str(e)}")
            import traceback
            traceback.print_exc()
        
        break

if __name__ == "__main__":
    asyncio.run(test_brand_context_loading())
```

### Test 4: Test Refresh Endpoint

```bash
# Get your admin token first (from login)
curl -X POST "http://localhost:8000/api/companies/{company_id}/refresh-brand-context" \
  -H "Authorization: Bearer YOUR_ADMIN_TOKEN" \
  -H "Content-Type: application/json"
```

**Expected response**:
```json
{
  "status": "success",
  "message": "Brand context refreshed successfully",
  "company_id": "...",
  "company_name": "...",
  "loaded_documents": [
    "COMPANY.md",
    "VOICE.md",
    "PLAYBOOKS.md",
    "POLICIES.md",
    "KNOWLEDGE.md",
    "TEMPLATES (12 files)"
  ],
  "total_documents": 6
}
```

### Test 5: Test Full Flow 1 with Brand Context

1. **Send a test email** via n8n workflow (or manually trigger email ingestion)
2. **Check logs** for brand context loading:
   ```
   INFO: Brand context loaded for company {company_id}
   ```
3. **Check the draft** - it should use brand voice and templates
4. **Check classification** - should include company name
5. **Check priority score** - should use SLA rules

### Test 6: Test Redis Caching

```python
import asyncio
from database import get_db
from services.brand_context_loader import brand_context_loader
from services.redis_cache import redis_cache
import time

async def test_caching():
    async for db in get_db():
        company_id = "your-company-id-here"
        
        # First load (should hit Drive)
        print("First load (should load from Drive)...")
        start = time.time()
        context1 = await brand_context_loader.load_all(db, company_id)
        time1 = time.time() - start
        print(f"Time: {time1:.2f}s")
        
        # Second load (should hit cache)
        print("\nSecond load (should load from cache)...")
        start = time.time()
        context2 = await brand_context_loader.load_all(db, company_id)
        time2 = time.time() - start
        print(f"Time: {time2:.2f}s")
        
        # Cache should be much faster
        if time2 < time1 * 0.5:
            print("✅ Cache is working (much faster)")
        else:
            print("⚠️ Cache might not be working")
        
        # Verify cache key exists
        cache_key = f"brand_context:{company_id}"
        cached = await redis_cache.get(cache_key)
        if cached:
            print("✅ Cache entry exists in Redis")
        else:
            print("❌ Cache entry not found in Redis")
        
        break

if __name__ == "__main__":
    asyncio.run(test_caching())
```

---

## Troubleshooting

### Issue: Folder not found

**Check**:
1. Folder name is exactly `"Brand Context Documents"` (case-sensitive)
2. Or folder name matches company name exactly
3. OAuth tokens are valid and have Drive access
4. Folder is not in trash

**Solution**: Create folder with exact name or rename existing folder

### Issue: Files not loading

**Check**:
1. File names are exact: `COMPANY.md`, `VOICE.md`, etc. (case-sensitive)
2. Files are in the root of the folder (not in subfolders)
3. Files are readable (not restricted permissions)

**Solution**: Rename files to match exact names

### Issue: Templates not loading

**Check**:
1. TEMPLATES folder exists (exact name, case-sensitive)
2. Template files are .md or text files
3. Subfolders are named correctly (outreach/, hiring/, responses/)

**Solution**: Verify folder structure matches expected format

### Issue: Redis connection failed

**Check**:
1. Redis Docker container is running: `docker ps | findstr redis`
2. Redis is accessible on localhost:6379
3. No firewall blocking connection

**Solution**: 
```bash
docker start redis
# Or restart if needed
docker restart redis
```

---

## Summary

### Hardcoded Names in Backend:
- **Folder**: `"Brand Context Documents"` (or company name as fallback)
- **Files**: `COMPANY.md`, `VOICE.md`, `PLAYBOOKS.md`, `POLICIES.md`, `KNOWLEDGE.md`
- **Template Folder**: `TEMPLATES`

### What You Need to Do:
1. ✅ **No code changes needed** - everything is implemented
2. ✅ **Create folder structure** in each company's Google Drive
3. ✅ **Upload files** with exact names
4. ✅ **Test** using the scripts above

### Next Steps:
1. Set up folder structure in Google Drive for one test company
2. Run test scripts to verify loading works
3. Test with a real email to see brand context in action
4. Monitor logs for any errors

