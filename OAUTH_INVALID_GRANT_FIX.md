# OAuth invalid_grant Error - Fix Guide

## 🔴 Problem

Getting `invalid_grant` error when exchanging authorization code for tokens in n8n workflow.

## 🔍 Root Causes

The `invalid_grant` error from Google OAuth can happen for several reasons:

1. **Authorization code already used** - Codes are single-use only
2. **Authorization code expired** - Codes expire within minutes
3. **redirect_uri mismatch** - Must EXACTLY match the one used in initial request
4. **URL encoding issues** - Special characters or encoding problems
5. **Client ID/Secret mismatch** - Wrong credentials

## ✅ Fixes Applied

### 1. Hardcoded redirect_uri in Token Exchange

**Changed:** Instead of using `={{ $json.redirect_uri }}` from previous node, now using hardcoded value to ensure exact match.

**Why:** This ensures the redirect_uri is EXACTLY the same as what was used in the frontend OAuth request.

**Before:**
```json
{
  "name": "redirect_uri",
  "value": "={{ $json.redirect_uri }}"
}
```

**After:**
```json
{
  "name": "redirect_uri",
  "value": "http://localhost:5678/webhook/oauth-callback"
}
```

### 2. Added Response Format Options

Added response format options to get better error messages from Google.

## ⚠️ CRITICAL: Verify Google Cloud Console

**You MUST verify these settings in Google Cloud Console:**

1. **Go to:** https://console.cloud.google.com/apis/credentials
2. **Click on your OAuth 2.0 Client ID**
3. **Check Authorized redirect URIs:**
   - ✅ Must have: `http://localhost:5678/webhook/oauth-callback`
   - ✅ Must be EXACT (no trailing slash, exact case)
   - ✅ Must match what's in frontend and workflow

4. **Verify Client ID and Secret:**
   - Client ID: `407115728261-22odd5dsa5grrtmdqena19bs5id0l0a5.apps.googleusercontent.com`
   - Make sure this matches your workflow

## 🧪 Testing Steps

### Step 1: Clear Browser Cache
Authorization codes are single-use. If you've already tried, the code is invalid.

1. **Clear browser cache/cookies** for Google
2. **Or use incognito/private window**

### Step 2: Verify Redirect URI in Google Console
1. Go to Google Cloud Console
2. Check that `http://localhost:5678/webhook/oauth-callback` is in authorized redirect URIs
3. Make sure there's NO trailing slash
4. Make sure it's exactly `http://localhost:5678/webhook/oauth-callback` (not `https://`)

### Step 3: Test OAuth Flow
1. Go to frontend: http://localhost:3000
2. Login as admin
3. Navigate to Companies page
4. Click "Add Company"
5. Enter company name
6. Click "Connect Gmail & Drive"
7. **Complete OAuth in ONE go** - don't refresh or go back
8. Should work now!

## 🔧 Additional Troubleshooting

### If Still Getting invalid_grant:

1. **Check n8n Workflow Execution Logs:**
   - Look at the "Exchange Code for Tokens" node
   - Check what redirect_uri is being sent
   - Verify it matches exactly

2. **Verify Frontend Redirect URI:**
   - Check `frontend/src/components/AddCompanyModal.tsx`
   - Should be: `http://localhost:5678/webhook/oauth-callback`
   - No trailing slash

3. **Check for Multiple Workflow Executions:**
   - If workflow runs multiple times with same code, it will fail
   - Each OAuth flow should only run once

4. **Verify Client Secret:**
   - Make sure the client_secret in workflow matches Google Console
   - Client secrets can be regenerated - make sure you're using the current one

## 📝 Common Mistakes

❌ **Wrong:** `http://localhost:5678/webhook/oauth-callback/` (trailing slash)
✅ **Correct:** `http://localhost:5678/webhook/oauth-callback`

❌ **Wrong:** `https://localhost:5678/webhook/oauth-callback` (https instead of http)
✅ **Correct:** `http://localhost:5678/webhook/oauth-callback`

❌ **Wrong:** Using code multiple times
✅ **Correct:** Each code can only be used once

❌ **Wrong:** Waiting too long (code expired)
✅ **Correct:** Exchange code immediately after receiving it

## ✅ Expected Flow

1. Frontend → Google OAuth with `redirect_uri=http://localhost:5678/webhook/oauth-callback`
2. Google → Redirects to n8n webhook with `code` and `state`
3. n8n Workflow → Extracts code
4. n8n Workflow → Exchanges code with `redirect_uri=http://localhost:5678/webhook/oauth-callback` (EXACT MATCH)
5. Google → Returns tokens
6. n8n Workflow → Registers company with backend

**The redirect_uri in step 1 and step 4 MUST be EXACTLY the same!**

