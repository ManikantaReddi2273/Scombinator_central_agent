# n8n Workflow Fix - redirect_uri_mismatch Error

## ✅ Issue Fixed

**Problem**: `redirect_uri_mismatch` error when exchanging OAuth code for tokens

**Root Cause**: 
- Frontend was using: `http://localhost:5678/rest/oauth2-credential/callback`
- Webhook is at: `http://localhost:5678/webhook/oauth-callback`
- These didn't match!

**Solution**: 
- Updated frontend to use: `http://localhost:5678/webhook/oauth-callback`
- Updated workflow to use the same redirect_uri

---

## 🔄 Changes Made

### 1. Frontend (`frontend/src/components/AddCompanyModal.tsx`)
- Changed default redirect_uri from `http://localhost:5678/rest/oauth2-credential/callback` 
- To: `http://localhost:5678/webhook/oauth-callback`

### 2. Workflow (`Company Onboarding.json`)
- Updated JavaScript code to use: `http://localhost:5678/webhook/oauth-callback`
- Added comment explaining the redirect_uri must match exactly

---

## ⚠️ IMPORTANT: Update Google Cloud Console

You **MUST** add this redirect URI to your Google Cloud Console:

1. Go to: https://console.cloud.google.com/apis/credentials?project=scombinator
2. Click on your OAuth 2.0 Client ID
3. Under **Authorized redirect URIs**, make sure you have:
   - ✅ `http://localhost:5678/webhook/oauth-callback` (REQUIRED - for workflow)
   - ✅ `http://localhost:5678/rest/oauth2-credential/callback` (optional - for n8n credential system)

4. Click **SAVE**

---

## 🧪 Testing the Fix

### Step 1: Update Google Cloud Console
Add the redirect URI as shown above.

### Step 2: Restart Frontend (if running)
```powershell
# Stop frontend (Ctrl+C)
# Restart it to pick up the new redirect_uri
cd frontend
npm run dev
```

### Step 3: Test OAuth Flow

1. Go to: http://localhost:3000
2. Login as admin
3. Navigate to **Companies** page
4. Click **Add Company**
5. Enter company name
6. Click **Connect Gmail & Drive**
7. Should redirect to Google OAuth
8. Sign in with company Gmail
9. Grant permissions
10. Should redirect back and company should be registered

---

## 🔍 Workflow Flow (After Fix)

1. **Frontend** → Redirects to Google OAuth with `redirect_uri=http://localhost:5678/webhook/oauth-callback`
2. **Google** → User authorizes → Redirects to `http://localhost:5678/webhook/oauth-callback?code=XXX&state=CompanyName`
3. **n8n Webhook** → Receives callback at `/webhook/oauth-callback`
4. **Code Node** → Extracts code and sets `redirect_uri=http://localhost:5678/webhook/oauth-callback`
5. **HTTP Request** → Exchanges code for tokens using the SAME redirect_uri ✅
6. **Code Node 1** → Extracts tokens
7. **HTTP Request 1** → Gets user info
8. **Code Node 2** → Combines data
9. **HTTP Request 2** → Registers company in backend
10. **Respond to Webhook** → Redirects to frontend

---

## ✅ Verification Checklist

- [ ] Google Cloud Console has `http://localhost:5678/webhook/oauth-callback` in authorized redirect URIs
- [ ] Frontend code updated (already done)
- [ ] Workflow code updated (already done)
- [ ] Frontend restarted (if it was running)
- [ ] Test OAuth flow end-to-end

---

**After updating Google Cloud Console, the workflow should work!** 🚀

