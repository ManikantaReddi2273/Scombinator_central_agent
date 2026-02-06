# 🚀 Complete Google OAuth Setup Instructions

## Overview

You need to set up Google OAuth to connect company Gmail and Drive accounts to your S Combinator platform. This guide walks you through everything step-by-step.

---

## 📋 What You'll Do

1. ✅ Create Google OAuth credentials in Google Cloud Console
2. ✅ Configure redirect URIs
3. ✅ Add credentials to frontend
4. ✅ Update n8n workflow
5. ✅ Test the flow

---

## 🔵 PART 1: Google Cloud Console Setup

### Step 1: Enable APIs

1. Go to: **https://console.cloud.google.com/welcome?project=scombinator**
2. Sign in with: `reddimanikanta2005@gmail.com`
3. Click **☰ Menu** → **APIs & Services** → **Library**
4. Search and enable:
   - ✅ **Gmail API** - Click → Enable
   - ✅ **Google Drive API** - Click → Enable

### Step 2: Configure OAuth Consent Screen

1. Go to: **APIs & Services** → **OAuth consent screen**
2. Select: **External** → **Create**
3. Fill in:
   - **App name**: `S Combinator Central Agent Platform`
   - **User support email**: `reddimanikanta2005@gmail.com`
   - **Developer contact**: `reddimanikanta2005@gmail.com`
4. Click **Save and Continue**
5. **Add Scopes** (Step 2):
   - Click **Add or Remove Scopes**
   - Add these 4 scopes:
     - `https://www.googleapis.com/auth/gmail.readonly`
     - `https://www.googleapis.com/auth/gmail.send`
     - `https://www.googleapis.com/auth/drive.readonly`
     - `https://www.googleapis.com/auth/drive.file`
   - Click **Update** → **Save and Continue**
6. **Add Test Users** (Step 3):
   - Click **+ Add Users**
   - Enter: `reddimanikanta2005@gmail.com`
   - Click **Add** → **Save and Continue**
7. **Summary** (Step 4): Click **Back to Dashboard**

### Step 3: Create OAuth Client ID

1. Go to: **APIs & Services** → **Credentials**
2. Click **+ CREATE CREDENTIALS** → **OAuth client ID**
3. Fill in:
   - **Application type**: `Web application`
   - **Name**: `S Combinator n8n OAuth Client`
   - **Authorized JavaScript origins**: 
     - Click **+ ADD URI** → `http://localhost:5678`
     - Click **+ ADD URI** → `http://localhost:3000`
   - **Authorized redirect URIs** (IMPORTANT - Add BOTH):
     - Click **+ ADD URI** → `http://localhost:5678/rest/oauth2-credential/callback`
     - Click **+ ADD URI** → `http://localhost:5678/webhook/oauth-callback`
4. Click **CREATE**
5. **⚠️ COPY YOUR CREDENTIALS NOW!**
   - **Client ID**: `XXXXXXXXXX-XXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXX.apps.googleusercontent.com`
   - **Client secret**: `GOCSPX-XXXXXXXXXXXXXXXXXXXXXXXXX`
   - Save them somewhere safe (you won't see the secret again!)
6. Click **OK**

---

## 🔵 PART 2: Frontend Configuration

### Step 1: Create .env File

1. Navigate to: `frontend/` folder
2. Create a new file named: `.env`
3. Add this content:

```env
VITE_API_URL=http://localhost:8000
VITE_GOOGLE_CLIENT_ID=PASTE_YOUR_CLIENT_ID_HERE
VITE_N8N_CALLBACK_URL=http://localhost:5678/rest/oauth2-credential/callback
```

4. Replace `PASTE_YOUR_CLIENT_ID_HERE` with your actual Client ID from Part 1, Step 3

**Example:**
```env
VITE_API_URL=http://localhost:8000
VITE_GOOGLE_CLIENT_ID=123456789-abcdefghijklmnopqrstuvwxyz.apps.googleusercontent.com
VITE_N8N_CALLBACK_URL=http://localhost:5678/rest/oauth2-credential/callback
```

### Step 2: Restart Frontend

After creating `.env`, restart your frontend dev server:
```bash
cd frontend
npm run dev
```

---

## 🔵 PART 3: n8n Workflow Configuration

### Option A: Update Workflow JSON (Current Method)

1. Open file: `Company Onboarding.json`
2. Find **Line 48** (client_id):
   ```json
   "value": "407115728261-cosvsli6mooddouisakt51g4m6e599ir.apps.googleusercontent.com"
   ```
   Replace with your Client ID:
   ```json
   "value": "YOUR_CLIENT_ID_HERE.apps.googleusercontent.com"
   ```

3. Find **Line 52** (client_secret):
   ```json
   "value": "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"
   ```
   Replace with your Client Secret:
   ```json
   "value": "GOCSPX-YOUR_CLIENT_SECRET_HERE"
   ```

4. **✅ Already Updated**: The redirect URI is already set to `http://localhost:5678/rest/oauth2-credential/callback`

5. Import the updated workflow in n8n:
   - Go to: http://localhost:5678
   - Click **Workflows** → **Import from File**
   - Select `Company Onboarding.json`
   - Click **Import**

### Option B: Use n8n Credential System (Recommended)

Instead of hardcoding, use n8n's secure credential storage:

1. In n8n UI (http://localhost:5678):
   - Go to **Credentials** (left sidebar)
   - Click **+ Add Credential**
   - Search: `OAuth2 API`
   - Fill in:
     - **Credential Name**: `Google OAuth - S Combinator`
     - **Client ID**: `YOUR_CLIENT_ID`
     - **Client Secret**: `YOUR_CLIENT_SECRET`
     - **Authorization URL**: `https://accounts.google.com/o/oauth2/v2/auth`
     - **Access Token URL**: `https://oauth2.googleapis.com/token`
     - **Scope**: 
       ```
       https://www.googleapis.com/auth/gmail.readonly https://www.googleapis.com/auth/gmail.send https://www.googleapis.com/auth/drive.readonly https://www.googleapis.com/auth/drive.file
       ```
     - **Redirect URI**: `http://localhost:5678/rest/oauth2-credential/callback`
   - Click **Save**

2. Update workflow to use this credential instead of hardcoded values

---

## 🔵 PART 4: Test the Flow

### Step 1: Start All Services

**Terminal 1 - Backend:**
```bash
cd backend
python main.py
```

**Terminal 2 - Frontend:**
```bash
cd frontend
npm run dev
```

**Terminal 3 - n8n (if not running):**
```bash
cd n8n
docker-compose up -d
```

### Step 2: Test OAuth Flow

1. Open browser: http://localhost:3000
2. **Login** as admin:
   - Email: `reddimanikanta2005@gmail.com`
   - Password: `R@ddi2273`
3. Navigate to: **Companies** page (left sidebar)
4. Click: **Add Company** button (top right)
5. Enter company name (e.g., "TestCompany")
6. Click: **Connect Gmail & Drive** button
7. **Expected behavior**:
   - ✅ Redirects to Google OAuth login
   - ✅ Sign in with company Gmail account
   - ✅ Grant permissions (Gmail + Drive)
   - ✅ Redirects back to frontend
   - ✅ Company appears in Companies list

---

## ✅ Verification Checklist

Before testing, verify:

- [ ] Gmail API enabled in Google Cloud Console
- [ ] Google Drive API enabled in Google Cloud Console
- [ ] OAuth consent screen configured
- [ ] OAuth client ID created
- [ ] Both redirect URIs added to Google Console:
  - [ ] `http://localhost:5678/rest/oauth2-credential/callback`
  - [ ] `http://localhost:5678/webhook/oauth-callback`
- [ ] Client ID and Secret copied
- [ ] `frontend/.env` file created with Client ID
- [ ] `Company Onboarding.json` updated with credentials
- [ ] n8n workflow imported/updated
- [ ] All services running (backend, frontend, n8n)

---

## 🐛 Troubleshooting

### Error: "redirect_uri_mismatch"

**Problem**: Redirect URI doesn't match

**Solution**:
1. Go to Google Cloud Console → Credentials
2. Click on your OAuth client ID
3. Verify both redirect URIs are added:
   - `http://localhost:5678/rest/oauth2-credential/callback`
   - `http://localhost:5678/webhook/oauth-callback`
4. Make sure there are no typos or extra spaces

### Error: "invalid_client"

**Problem**: Client ID or Secret is wrong

**Solution**:
1. Verify Client ID in `frontend/.env` matches Google Console
2. Verify Client ID and Secret in `Company Onboarding.json` are correct
3. Check for extra spaces when copying

### Error: "access_denied"

**Problem**: User not authorized or test user not added

**Solution**:
1. Go to OAuth consent screen → Test users
2. Make sure `reddimanikanta2005@gmail.com` is added
3. Try again

### No Refresh Token Received

**Problem**: Missing `access_type=offline` or `prompt=consent`

**Solution**: Already handled in code! The frontend includes both parameters.

---

## 📁 Files Summary

### Files Already Updated ✅:
- `frontend/src/components/AddCompanyModal.tsx` - Uses correct redirect URI
- `frontend/src/vite-env.d.ts` - TypeScript types for env variables
- `Company Onboarding.json` - Redirect URI updated

### Files You Need to Create/Update:
- `frontend/.env` - **CREATE THIS** with your Client ID
- `Company Onboarding.json` - **UPDATE** lines 48 and 52 with your credentials

---

## 🔐 Security Notes

1. **Never commit `.env` to Git** - It's already in `.gitignore`
2. **Never share Client Secret** publicly
3. **Use n8n Credential System** instead of hardcoding (recommended)
4. **Rotate credentials** if compromised

---

## 📚 Additional Documentation

- **GOOGLE_OAUTH_SETUP_GUIDE.md** - Complete technical guide
- **GOOGLE_CLOUD_CONSOLE_STEPS.md** - Detailed console instructions
- **QUICK_START_OAUTH.md** - 5-minute quick reference
- **OAUTH_SETUP_SUMMARY.md** - Overview and checklist

---

## 🎯 Quick Reference

**Google Cloud Console**: https://console.cloud.google.com/welcome?project=scombinator

**Redirect URIs to Add**:
- `http://localhost:5678/rest/oauth2-credential/callback`
- `http://localhost:5678/webhook/oauth-callback`

**Where to Put Credentials**:
- Frontend: `frontend/.env` (Client ID only)
- n8n Workflow: `Company Onboarding.json` (Client ID + Secret)

---

**Ready to start?** Begin with Part 1 above! 🚀

