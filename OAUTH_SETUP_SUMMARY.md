# Google OAuth Setup - Complete Summary

## 📍 Your Configuration

- **Admin Email**: `reddimanikanta2005@gmail.com`
- **Google Cloud Project**: `scombinator`
- **n8n URL**: `http://localhost:5678`
- **Frontend URL**: `http://localhost:3000`
- **Backend URL**: `http://localhost:8000`
- **OAuth Redirect URI**: `http://localhost:5678/rest/oauth2-credential/callback`

---

## ✅ What You Need to Do

### Step 1: Google Cloud Console Setup (15 minutes)

1. **Enable APIs**
   - Gmail API
   - Google Drive API

2. **Configure OAuth Consent Screen**
   - App name: `S Combinator Central Agent Platform`
   - Support email: `reddimanikanta2005@gmail.com`
   - Add scopes (Gmail + Drive)
   - Add test user: `reddimanikanta2005@gmail.com`

3. **Create OAuth Client ID**
   - Type: Web application
   - Name: `S Combinator n8n OAuth Client`
   - **Authorized redirect URIs** (add both):
     - `http://localhost:5678/rest/oauth2-credential/callback`
     - `http://localhost:5678/webhook/oauth-callback`
   - **Copy Client ID and Secret!**

**📖 Detailed steps**: See `GOOGLE_CLOUD_CONSOLE_STEPS.md`

---

### Step 2: Frontend Configuration (2 minutes)

Create `frontend/.env` file:

```env
VITE_API_URL=http://localhost:8000
VITE_GOOGLE_CLIENT_ID=YOUR_CLIENT_ID_HERE.apps.googleusercontent.com
VITE_N8N_CALLBACK_URL=http://localhost:5678/rest/oauth2-credential/callback
```

Replace `YOUR_CLIENT_ID_HERE` with your actual Client ID.

**✅ Already updated**: `frontend/src/components/AddCompanyModal.tsx` uses the correct redirect URI.

---

### Step 3: n8n Workflow Configuration (5 minutes)

**Option A: Update Workflow JSON** (Current approach)

Edit `Company Onboarding.json`:
- **Line 48**: Update `client_id` value
- **Line 52**: Update `client_secret` value

**✅ Already updated**: Redirect URI changed to `http://localhost:5678/rest/oauth2-credential/callback`

**Option B: Use n8n Credential System** (Recommended)

1. In n8n UI → Credentials → Add Credential
2. Select: OAuth2 API
3. Fill in your Client ID and Secret
4. Update workflow to use this credential instead of hardcoded values

---

### Step 4: Test the Flow (5 minutes)

1. **Start services**:
   ```bash
   # Terminal 1: Backend
   cd backend
   python main.py
   
   # Terminal 2: Frontend
   cd frontend
   npm run dev
   
   # Terminal 3: n8n (if not running)
   cd n8n
   docker-compose up -d
   ```

2. **Test OAuth**:
   - Go to: http://localhost:3000
   - Login as admin
   - Navigate to: **Companies** page
   - Click: **Add Company**
   - Enter company name
   - Click: **Connect Gmail & Drive**
   - Should redirect to Google OAuth
   - Sign in with company Gmail
   - Grant permissions
   - Should redirect back to frontend

---

## 📁 Files Updated

### ✅ Already Updated:
1. `frontend/src/components/AddCompanyModal.tsx` - Uses correct redirect URI
2. `Company Onboarding.json` - Redirect URI updated

### 📝 Files You Need to Create/Update:
1. `frontend/.env` - Add your Client ID
2. `Company Onboarding.json` - Add your Client ID and Secret (lines 48, 52)

---

## 🔐 Where to Put Credentials

| Location | What Goes There | Example |
|----------|----------------|---------|
| `frontend/.env` | Client ID only | `VITE_GOOGLE_CLIENT_ID=123...apps.googleusercontent.com` |
| `Company Onboarding.json` | Client ID + Secret | Lines 48, 52 |
| Google Cloud Console | Both (already there) | Credentials page |

**⚠️ Security**: Never commit `.env` or credentials to Git!

---

## 🎯 Quick Checklist

- [ ] Enabled Gmail API in Google Cloud Console
- [ ] Enabled Google Drive API in Google Cloud Console
- [ ] Configured OAuth consent screen
- [ ] Created OAuth client ID
- [ ] Added redirect URIs to Google Console:
  - [ ] `http://localhost:5678/rest/oauth2-credential/callback`
  - [ ] `http://localhost:5678/webhook/oauth-callback`
- [ ] Copied Client ID and Secret
- [ ] Created `frontend/.env` with Client ID
- [ ] Updated `Company Onboarding.json` with credentials
- [ ] Tested OAuth flow end-to-end

---

## 🐛 Common Issues

### "redirect_uri_mismatch"
- **Fix**: Make sure both redirect URIs are added in Google Cloud Console → Credentials → OAuth Client

### "invalid_client"
- **Fix**: Verify Client ID and Secret are correct in workflow JSON

### "access_denied"
- **Fix**: Add your email to OAuth consent screen → Test users

### No refresh token
- **Fix**: Already handled in code (`access_type=offline` and `prompt=consent`)

---

## 📚 Documentation Files

1. **GOOGLE_OAUTH_SETUP_GUIDE.md** - Complete setup guide
2. **GOOGLE_CLOUD_CONSOLE_STEPS.md** - Detailed console steps
3. **QUICK_START_OAUTH.md** - 5-minute quick start
4. **OAUTH_SETUP_SUMMARY.md** - This file (overview)

---

## 🚀 Next Steps After Setup

1. Test company onboarding flow
2. Verify tokens are stored encrypted in database
3. Test email processing workflow
4. Configure n8n email trigger workflow
5. Test draft approval flow

---

## 💡 Pro Tips

1. **Use n8n Credential System**: Instead of hardcoding in workflow JSON, use n8n's encrypted credential store
2. **Test in Incognito**: Use incognito browser to test OAuth flow
3. **Check Logs**: Monitor n8n logs and backend logs for errors
4. **Backup Credentials**: Save Client ID and Secret in a password manager

---

**Need Help?** Check the detailed guides or review the error messages in browser console and n8n logs.

**Last Updated**: 2026-02-04

