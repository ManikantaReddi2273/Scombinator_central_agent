# Fresh Company Onboarding Workflow - Complete Guide

## ✅ New Clean Workflow Created

I've completely rewritten the workflow from scratch with a clean, simple flow.

---

## 🔄 Workflow Flow (8 Nodes)

### Node 1: Webhook
- **Type**: Webhook
- **Path**: `oauth-callback`
- **Purpose**: Receives OAuth callback from Google
- **Receives**: `?code=XXX&state=CompanyName`

### Node 2: Extract OAuth Code
- **Type**: Code (JavaScript)
- **Purpose**: Extracts code and company name from webhook
- **Output**: `{ code, company_name, redirect_uri }`

### Node 3: Exchange Code for Tokens
- **Type**: HTTP Request
- **Method**: POST
- **URL**: `https://oauth2.googleapis.com/token`
- **Body**: Form-urlencoded with:
  - `code`
  - `client_id`
  - `client_secret`
  - `redirect_uri` (must match frontend!)
  - `grant_type: authorization_code`
- **Output**: `{ access_token, refresh_token, expires_in }`

### Node 4: Extract Tokens
- **Type**: Code (JavaScript)
- **Purpose**: Extracts tokens and prepares data
- **Output**: `{ company_name, access_token, refresh_token, expires_in, n8n_credential_id }`

### Node 5: Get User Email
- **Type**: HTTP Request
- **Method**: GET
- **URL**: `https://www.googleapis.com/oauth2/v2/userinfo`
- **Headers**: `Authorization: Bearer {access_token}`
- **Output**: `{ email, ... }`

### Node 6: Prepare Registration Data
- **Type**: Code (JavaScript)
- **Purpose**: Combines all data for backend
- **Output**: `{ company_name, email, access_token, refresh_token, n8n_credential_id, expires_in }`

### Node 7: Register Company
- **Type**: HTTP Request
- **Method**: POST
- **URL**: `http://localhost:8000/api/companies/register`
- **Headers**: `Content-Type: application/json`
- **Body**: JSON with all company data
- **Output**: Company record from backend

### Node 8: Redirect to Frontend
- **Type**: Respond to Webhook
- **Purpose**: Redirects browser back to frontend
- **URL**: `http://localhost:3000/companies?success=true&company=CompanyName`

---

## 📋 Key Features

### ✅ Clean Structure
- Only 8 nodes (no unnecessary nodes)
- Clear naming for each node
- Logical flow from start to finish

### ✅ Proper Error Handling
- Validates code exists
- Validates token response
- Validates user email
- Clear error messages

### ✅ Correct Parameters
- `redirect_uri` matches frontend exactly
- All required fields sent to backend
- Proper JSON formatting

### ✅ Data Flow
- Each node passes data to next
- Uses n8n's node reference system
- Proper data extraction and transformation

---

## 🚀 Setup Instructions

### Step 1: Import Workflow

1. Open n8n: http://localhost:5678
2. Go to **Workflows**
3. Click **Import from File**
4. Select `Company Onboarding.json`
5. Click **Import**

### Step 2: Activate Workflow

1. Click the **Active** toggle (top right)
2. Workflow should show as "Active"

### Step 3: Get Webhook URL

1. Click on the **Webhook** node
2. Copy the **Production URL** or **Test URL**
3. Should be: `http://localhost:5678/webhook/oauth-callback`

### Step 4: Verify Configuration

**Check these in the workflow:**

1. **Exchange Code for Tokens node:**
   - Client ID: `407115728261-22odd5dsa5grrtmdqena19bs5id0l0a5.apps.googleusercontent.com`
   - Client Secret: `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`
   - redirect_uri: `http://localhost:5678/webhook/oauth-callback`

2. **Register Company node:**
   - URL: `http://localhost:8000/api/companies/register`
   - Method: POST
   - Content-Type: application/json

---

## 🧪 Testing

### Test the Workflow

1. **Go to frontend**: http://localhost:3000
2. **Login** as admin
3. **Navigate** to Companies page
4. **Click** "Add Company"
5. **Enter** company name (e.g., "TestCompany")
6. **Click** "Connect Gmail & Drive"
7. **Should redirect** to Google OAuth
8. **Sign in** with company Gmail
9. **Grant permissions**
10. **Should redirect** back to frontend
11. **Company should appear** in list

### Check n8n Execution

1. Go to n8n: http://localhost:5678
2. Click **Executions** (left sidebar)
3. Find the latest execution
4. Click on it to see details
5. Check each node:
   - ✅ Green = Success
   - ❌ Red = Error (check error message)

---

## 🐛 Troubleshooting

### Error: "redirect_uri_mismatch"
- **Check**: Google Cloud Console has `http://localhost:5678/webhook/oauth-callback`
- **Check**: Frontend uses same redirect_uri
- **Check**: Workflow uses same redirect_uri

### Error: "No authorization code received"
- **Check**: Webhook is receiving the callback
- **Check**: Google is redirecting correctly
- **Check**: Webhook path matches redirect_uri

### Error: "Failed to get access token"
- **Check**: Client ID and Secret are correct
- **Check**: Code hasn't expired (codes expire quickly)
- **Check**: redirect_uri matches exactly

### Error: "Failed to get user email"
- **Check**: Access token is valid
- **Check**: Token has userinfo scope
- **Check**: Google API is accessible

### Error: "Company registration failed"
- **Check**: Backend is running on port 8000
- **Check**: Database is accessible
- **Check**: Backend logs for errors

---

## ✅ Verification Checklist

- [ ] Workflow imported in n8n
- [ ] Workflow is activated
- [ ] Webhook URL is: `http://localhost:5678/webhook/oauth-callback`
- [ ] Client ID and Secret are correct in workflow
- [ ] redirect_uri matches in all places
- [ ] Backend URL is correct: `http://localhost:8000/api/companies/register`
- [ ] Google Cloud Console has redirect_uri
- [ ] Frontend uses correct redirect_uri
- [ ] Test OAuth flow end-to-end

---

## 📊 Node Summary

| Node | Type | Purpose | Status |
|------|------|---------|--------|
| Webhook | Webhook | Receive OAuth callback | ✅ Required |
| Extract OAuth Code | Code | Extract code & state | ✅ Required |
| Exchange Code for Tokens | HTTP Request | Get tokens from Google | ✅ Required |
| Extract Tokens | Code | Process token response | ✅ Required |
| Get User Email | HTTP Request | Get user email | ✅ Required |
| Prepare Registration Data | Code | Combine all data | ✅ Required |
| Register Company | HTTP Request | Save to backend | ✅ Required |
| Redirect to Frontend | Respond | Redirect browser | ✅ Required |

**All 8 nodes are necessary - none should be deleted!**

---

**The workflow is now clean, simple, and should work correctly!** 🚀

