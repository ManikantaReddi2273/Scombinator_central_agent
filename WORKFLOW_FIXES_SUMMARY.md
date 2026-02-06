# n8n Workflow Fixes - Complete Summary

## ✅ Issues Fixed

### 1. **redirect_uri_mismatch Error** (CRITICAL)
- **Problem**: Frontend and workflow were using different redirect URIs
- **Fix**: 
  - Updated frontend to use: `http://localhost:5678/webhook/oauth-callback`
  - Updated workflow to use the same redirect_uri
  - Both now match the webhook path

### 2. **Missing expires_in Parameter**
- **Problem**: Workflow wasn't sending `expires_in` to backend
- **Fix**: Added `expires_in` to the HTTP Request2 body

---

## 📝 Files Changed

### 1. `frontend/src/components/AddCompanyModal.tsx`
**Changed:**
```typescript
// OLD:
const redirectUri = 'http://localhost:5678/rest/oauth2-credential/callback'

// NEW:
const redirectUri = 'http://localhost:5678/webhook/oauth-callback'
```

### 2. `Company Onboarding.json`
**Changed:**
1. **Code in JavaScript node** - Updated redirect_uri:
   ```javascript
   // OLD:
   redirect_uri: 'http://localhost:5678/rest/oauth2-credential/callback'
   
   // NEW:
   redirect_uri: 'http://localhost:5678/webhook/oauth-callback'
   ```

2. **HTTP Request2 node** - Added expires_in:
   ```json
   // OLD:
   {
     "company_name": "...",
     "email": "...",
     "access_token": "...",
     "refresh_token": "...",
     "n8n_credential_id": "..."
   }
   
   // NEW:
   {
     "company_name": "...",
     "email": "...",
     "access_token": "...",
     "refresh_token": "...",
     "n8n_credential_id": "...",
     "expires_in": {{ $json.expires_in }}
   }
   ```

---

## ⚠️ REQUIRED: Update Google Cloud Console

**You MUST add the redirect URI to Google Cloud Console:**

1. Go to: https://console.cloud.google.com/apis/credentials?project=scombinator
2. Click on your OAuth 2.0 Client ID
3. Under **Authorized redirect URIs**, click **+ ADD URI**
4. Add: `http://localhost:5678/webhook/oauth-callback`
5. Click **SAVE**

**Your authorized redirect URIs should now have:**
- ✅ `http://localhost:5678/webhook/oauth-callback` (REQUIRED - for workflow)
- ✅ `http://localhost:5678/rest/oauth2-credential/callback` (optional - for n8n credential system)

---

## 🔄 Workflow Flow (Corrected)

1. **Frontend** (`AddCompanyModal.tsx`)
   - User enters company name
   - Clicks "Connect Gmail & Drive"
   - Redirects to: `https://accounts.google.com/o/oauth2/v2/auth?...&redirect_uri=http://localhost:5678/webhook/oauth-callback&...`

2. **Google OAuth**
   - User authorizes
   - Google redirects to: `http://localhost:5678/webhook/oauth-callback?code=XXX&state=CompanyName`

3. **n8n Webhook** (`/webhook/oauth-callback`)
   - Receives callback with code and state
   - Triggers workflow

4. **Code in JavaScript**
   - Extracts `code` and `state` (company name)
   - Sets `redirect_uri: 'http://localhost:5678/webhook/oauth-callback'` ✅

5. **HTTP Request** (Token Exchange)
   - POST to `https://oauth2.googleapis.com/token`
   - Sends: `code`, `client_id`, `client_secret`, `redirect_uri`, `grant_type`
   - **redirect_uri matches what was used in step 1** ✅

6. **Code in JavaScript1**
   - Extracts `access_token`, `refresh_token`, `expires_in`
   - Gets company name from previous node
   - Generates `n8n_credential_id`

7. **HTTP Request1** (Get User Info)
   - GET to `https://www.googleapis.com/oauth2/v2/userinfo`
   - Uses `access_token` to get user email

8. **Code in JavaScript2**
   - Combines: company_name, email, tokens, credential_id, expires_in

9. **HTTP Request2** (Register Company)
   - POST to `http://localhost:8000/api/companies/register`
   - Sends: company_name, email, access_token, refresh_token, n8n_credential_id, **expires_in** ✅

10. **Respond to Webhook**
    - Redirects to: `http://localhost:3000/companies?success=true&company=CompanyName`

---

## 🧪 Testing Steps

### Step 1: Update Google Cloud Console
- Add `http://localhost:5678/webhook/oauth-callback` to authorized redirect URIs
- Save changes

### Step 2: Update Frontend .env (if needed)
Make sure `frontend/.env` has:
```env
VITE_N8N_CALLBACK_URL=http://localhost:5678/webhook/oauth-callback
```

### Step 3: Re-import Workflow in n8n
1. Open n8n: http://localhost:5678
2. Go to **Workflows**
3. Delete old "Company Onboarding" workflow (if exists)
4. Click **Import from File**
5. Select `Company Onboarding.json`
6. Click **Import**
7. **Activate** the workflow

### Step 4: Restart Frontend (if running)
```powershell
# Stop frontend (Ctrl+C)
cd frontend
npm run dev
```

### Step 5: Test OAuth Flow
1. Go to: http://localhost:3000
2. Login as admin
3. Navigate to **Companies**
4. Click **Add Company**
5. Enter company name (e.g., "TestCompany")
6. Click **Connect Gmail & Drive**
7. Should redirect to Google OAuth
8. Sign in with company Gmail account
9. Grant permissions
10. Should redirect back to frontend
11. Company should appear in Companies list

---

## ✅ Verification Checklist

- [ ] Google Cloud Console has `http://localhost:5678/webhook/oauth-callback` in authorized redirect URIs
- [ ] Frontend code updated (✅ already done)
- [ ] Workflow JSON updated (✅ already done)
- [ ] Workflow re-imported in n8n
- [ ] Workflow is activated in n8n
- [ ] Frontend restarted (if it was running)
- [ ] Backend is running on port 8000
- [ ] Test OAuth flow end-to-end

---

## 🐛 If Still Getting Errors

### Error: "redirect_uri_mismatch"
- **Check**: Google Cloud Console has the exact redirect URI
- **Check**: Frontend and workflow use the same redirect_uri
- **Check**: No typos or extra spaces

### Error: "Bad request - please check your parameters"
- **Check**: Client ID and Secret are correct in workflow
- **Check**: All required parameters are being sent
- **Check**: Content-Type is `application/x-www-form-urlencoded` for token exchange

### Error: "Company registration failed"
- **Check**: Backend is running on port 8000
- **Check**: Database is accessible
- **Check**: Backend logs for error messages

---

## 📊 Workflow Nodes Summary

All nodes are **necessary** and in the correct order:

1. ✅ **Webhook** - Receives OAuth callback
2. ✅ **Code in JavaScript** - Extracts code and sets redirect_uri
3. ✅ **HTTP Request** - Exchanges code for tokens
4. ✅ **Code in JavaScript1** - Extracts tokens and prepares data
5. ✅ **HTTP Request1** - Gets user email from Google
6. ✅ **Code in JavaScript2** - Combines all data
7. ✅ **HTTP Request2** - Registers company in backend
8. ✅ **Respond to Webhook** - Redirects to frontend

**No nodes need to be deleted - all are required!**

---

**After updating Google Cloud Console and re-importing the workflow, everything should work!** 🚀

