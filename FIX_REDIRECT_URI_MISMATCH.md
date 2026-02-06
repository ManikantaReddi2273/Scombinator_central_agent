# Fix: redirect_uri_mismatch Error

## 🔍 The Problem

Google is showing: **Error 400: redirect_uri_mismatch**

This means the redirect URI in your OAuth request doesn't match what's configured in Google Cloud Console.

---

## ✅ Solution: Verify and Fix Redirect URI

### Step 1: Check What Redirect URI is Being Sent

1. **Open browser console** (F12)
2. **Go to Network tab**
3. **Try connecting OAuth again**
4. **Look for the request to `accounts.google.com`**
5. **Check the `redirect_uri` parameter** in the URL

**OR** check the URL in the address bar when you click "Connect Gmail & Drive":
- It should show: `redirect_uri=http://localhost:5678/webhook/oauth-connect`
- If it shows something else, that's the problem

---

### Step 2: Verify Google Cloud Console Has the Exact URI

1. Go to: https://console.cloud.google.com/apis/credentials?project=scombinator
2. Click your OAuth 2.0 Client ID
3. Check **"Authorized redirect URIs"**
4. **Must have EXACTLY**: `http://localhost:5678/webhook/oauth-connect`
   - No trailing slash
   - Must be `http` (not `https`)
   - Must match exactly (case-sensitive)

---

### Step 3: Check Frontend Environment Variable

1. **Make sure you created `frontend/.env` file** with:
   ```env
   VITE_N8N_CALLBACK_URL=http://localhost:5678/webhook/oauth-connect
   ```

2. **Restart frontend dev server**:
   - Stop it (Ctrl+C)
   - Start again: `npm run dev`

3. **Clear browser cache** or use **Incognito mode**

---

### Step 4: Common Issues

**Issue 1: Environment variable not loaded**
- Vite only loads `.env` on startup
- **Solution**: Restart dev server after creating/editing `.env`

**Issue 2: Typo in redirect URI**
- Check for trailing slashes: `oauth-connect/` ❌ vs `oauth-connect` ✅
- Check for `https` vs `http`: `https://localhost:5678` ❌ vs `http://localhost:5678` ✅
- Check for port mismatch: `:5679` ❌ vs `:5678` ✅

**Issue 3: Multiple redirect URIs in Google Console**
- Make sure `http://localhost:5678/webhook/oauth-connect` is in the list
- Don't remove the others, just make sure this one is there

---

## 🔧 Quick Fix Steps

1. **Create/Update `frontend/.env`**:
   ```env
   VITE_API_URL=http://localhost:8000
   VITE_GOOGLE_CLIENT_ID=407115728261-22odd5dsa5grrtmdqena19bs5id0l0a5.apps.googleusercontent.com
   VITE_N8N_CALLBACK_URL=http://localhost:5678/webhook/oauth-connect
   ```

2. **Verify Google Cloud Console** has:
   - ✅ `http://localhost:5678/webhook/oauth-connect`

3. **Restart frontend**:
   ```bash
   cd frontend
   npm run dev
   ```

4. **Clear browser cache** or use **Incognito**

5. **Test again**

---

## 🎯 Debug: Check What's Actually Being Sent

Add this to `frontend/src/pages/Companies.tsx` temporarily to see what redirect URI is being used:

```typescript
const handleConnectOAuth = (companyId: string) => {
  const clientId = import.meta.env.VITE_GOOGLE_CLIENT_ID || ''
  const redirectUri = import.meta.env.VITE_N8N_CALLBACK_URL || 'http://localhost:5678/webhook/oauth-connect'
  
  // DEBUG: Log the redirect URI
  console.log('Redirect URI being used:', redirectUri)
  console.log('Environment variable:', import.meta.env.VITE_N8N_CALLBACK_URL)
  
  // ... rest of the code
}
```

Then check browser console (F12) to see what value is being used.

---

## ✅ Expected Result

After fixing, when you click "Connect Gmail & Drive":

1. **Browser should redirect to Google** (not show error)
2. **After authorization, redirect to**: `http://localhost:5678/webhook/oauth-connect?code=...`
3. **n8n workflow should execute**
4. **Executions should appear in n8n**

