# OAuth 401 Authorization Error - Fix Guide

## 🔴 Problem

Getting `401 Authorization failed` error in "Get User Email" node with message:
"Request is missing required authentication credential. Expected OAuth 2 access token"

## 🔍 Root Causes

1. **Token Exchange Failed** - The "Exchange Code for Tokens" node failed (invalid_grant error), so there's no valid access_token
2. **Wrong Authorization Header Syntax** - Using `{{ }}` instead of `={{ }}` in n8n expressions
3. **Token Not Passed Correctly** - Access token not being extracted or passed between nodes
4. **Token Format Issue** - Bearer token not properly formatted

## ✅ Fixes Applied

### 1. Fixed Authorization Header Syntax

**Before:**
```json
{
  "name": "Authorization",
  "value": "Bearer {{ $json.access_token }}"
}
```

**After:**
```json
{
  "name": "Authorization",
  "value": "={{ 'Bearer ' + $json.access_token }}"
}
```

**Why:** n8n requires `={{ }}` syntax for expressions, not `{{ }}`. The old syntax wasn't evaluating, so the header was literally "Bearer {{ $json.access_token }}" instead of "Bearer <actual_token>".

### 2. Added Error Handling in Extract Tokens Node

Added checks to detect if token exchange failed:
```javascript
// Check if token exchange failed (error response)
if (tokenResponse.error) {
  throw new Error(`Token exchange failed: ${tokenResponse.error} - ${tokenResponse.error_description || ''}`);
}

// Validate access token is not empty
if (!accessToken || accessToken.trim() === '') {
  throw new Error('Access token is empty or invalid');
}
```

**Why:** If the token exchange fails, we need to catch it early and provide a clear error message instead of passing an empty/invalid token to the next node.

## ⚠️ CRITICAL: Fix Token Exchange First

**The 401 error is a **symptom** - the root cause is likely the `invalid_grant` error in the "Exchange Code for Tokens" node.

**You MUST fix the token exchange first:**

1. **Verify Google Cloud Console:**
   - Go to: https://console.cloud.google.com/apis/credentials
   - Check that `http://localhost:5678/webhook/oauth-callback` is in authorized redirect URIs
   - Must be EXACT match (no trailing slash, exact case)

2. **Clear Browser Cache:**
   - Authorization codes are single-use
   - If you've already tried, the code is invalid
   - Clear cache/cookies or use incognito mode

3. **Test Fresh OAuth Flow:**
   - Start completely fresh
   - Don't refresh or go back during OAuth
   - Complete in one go

## 🧪 Testing Steps

### Step 1: Verify Token Exchange Works

1. Import updated workflow into n8n
2. Test OAuth flow
3. Check "Exchange Code for Tokens" node:
   - Should show green checkmark
   - Should have `access_token` in output
   - Should NOT have `error` field

### Step 2: Verify Token Extraction

1. Check "Extract Tokens" node:
   - Should extract `access_token` successfully
   - Should NOT throw error about missing token

### Step 3: Verify Authorization Header

1. Check "Get User Email" node execution:
   - Look at the request headers
   - Should show: `Authorization: Bearer <actual_token>`
   - Should NOT show: `Authorization: Bearer {{ $json.access_token }}`

### Step 4: Test Complete Flow

1. Go to frontend: http://localhost:3000
2. Login as admin
3. Navigate to Companies
4. Click "Add Company"
5. Enter company name
6. Click "Connect Gmail & Drive"
7. Complete OAuth in one go
8. Should work end-to-end now!

## 🔧 Troubleshooting

### If Still Getting 401:

1. **Check Token Exchange Output:**
   - In n8n, click on "Exchange Code for Tokens" node
   - Check the output data
   - Should have `access_token` field
   - If it has `error` field, token exchange failed

2. **Check Extract Tokens Output:**
   - Click on "Extract Tokens" node
   - Check if `access_token` is present
   - Check if it's not empty

3. **Check Get User Email Request:**
   - Click on "Get User Email" node
   - Check execution details
   - Look at request headers
   - Verify Authorization header format

4. **Verify OAuth Scopes:**
   - Frontend should request: `userinfo.email` scope
   - Check `AddCompanyModal.tsx` scopes include email access

## 📝 Expected Flow

1. **Frontend** → Google OAuth with scopes including `userinfo.email`
2. **Google** → Redirects to n8n with `code`
3. **n8n: Exchange Code for Tokens** → Gets `access_token` ✅
4. **n8n: Extract Tokens** → Extracts `access_token` ✅
5. **n8n: Get User Email** → Uses `Bearer <token>` in header ✅
6. **Google API** → Returns user email ✅
7. **n8n: Register Company** → Sends to backend ✅

## ✅ Summary

- **Fixed:** Authorization header syntax (now uses proper n8n expression)
- **Fixed:** Error handling in token extraction
- **Still Need:** Fix token exchange (invalid_grant error) - this is the root cause

**The 401 error will be resolved once the token exchange succeeds!**

