# Google OAuth Setup Guide - S Combinator Platform

Complete step-by-step guide to set up Google OAuth for your S Combinator Central Agent Platform.

## 📋 Prerequisites

- Google account: `reddimanikanta2005@gmail.com`
- Google Cloud Project: `scombinator` (already created)
- n8n running on: `http://localhost:5678`
- Frontend running on: `http://localhost:3000`
- Backend running on: `http://localhost:8000`

---

## 🔵 STEP 1: Enable Required APIs in Google Cloud Console

1. **Go to Google Cloud Console**
   - Visit: https://console.cloud.google.com/welcome?project=scombinator
   - Sign in with: `reddimanikanta2005@gmail.com`

2. **Enable Gmail API**
   - Navigate to: **APIs & Services** → **Library**
   - Search for: `Gmail API`
   - Click on **Gmail API**
   - Click **Enable**

3. **Enable Google Drive API**
   - In the same **Library** page
   - Search for: `Google Drive API`
   - Click on **Google Drive API**
   - Click **Enable**

4. **Enable Google OAuth2 API** (if not already enabled)
   - Search for: `Google+ API` or `Identity Toolkit API`
   - Enable it

---

## 🔵 STEP 2: Create OAuth 2.0 Client ID

1. **Navigate to OAuth Consent Screen**
   - Go to: **APIs & Services** → **OAuth consent screen**
   - Select: **External** (unless you have Google Workspace)
   - Click **Create**

2. **Fill OAuth Consent Screen**
   - **App name**: `S Combinator Central Agent Platform`
   - **User support email**: `reddimanikanta2005@gmail.com`
   - **Developer contact information**: `reddimanikanta2005@gmail.com`
   - Click **Save and Continue**

3. **Add Scopes** (Step 2)
   - Click **Add or Remove Scopes**
   - Add these scopes:
     - `https://www.googleapis.com/auth/gmail.readonly`
     - `https://www.googleapis.com/auth/gmail.send`
     - `https://www.googleapis.com/auth/drive.readonly`
     - `https://www.googleapis.com/auth/drive.file`
   - Click **Update** → **Save and Continue**

4. **Test Users** (Step 3)
   - Click **Add Users**
   - Add: `reddimanikanta2005@gmail.com`
   - Click **Add** → **Save and Continue**

5. **Summary** (Step 4)
   - Review and click **Back to Dashboard**

---

## 🔵 STEP 3: Create OAuth 2.0 Credentials

1. **Navigate to Credentials**
   - Go to: **APIs & Services** → **Credentials**
   - Click **+ CREATE CREDENTIALS** → **OAuth client ID**

2. **Configure OAuth Client**
   - **Application type**: `Web application`
   - **Name**: `S Combinator n8n OAuth Client`
   - **Authorized JavaScript origins**: 
     - `http://localhost:5678`
     - `http://localhost:3000`
   
   - **Authorized redirect URIs** (IMPORTANT - Add ALL of these):
     ```
     http://localhost:5678/rest/oauth2-credential/callback
     http://localhost:5678/webhook/oauth-callback
     ```
   
   - Click **Create**

3. **Copy Credentials**
   - A popup will show your credentials:
     - **Client ID**: `YOUR_CLIENT_ID.apps.googleusercontent.com`
     - **Client secret**: `GOCSPX-XXXXXXXXXXXXX`
   - **IMPORTANT**: Copy both immediately (you won't see the secret again!)
   - Click **OK**

---

## 🔵 STEP 4: Configure Frontend (.env file)

1. **Create/Update Frontend .env file**
   - Location: `frontend/.env`
   - Create the file if it doesn't exist

2. **Add these variables**:
   ```env
   VITE_API_URL=http://localhost:8000
   VITE_GOOGLE_CLIENT_ID=YOUR_CLIENT_ID_HERE.apps.googleusercontent.com
   VITE_N8N_CALLBACK_URL=http://localhost:5678/rest/oauth2-credential/callback
   ```

3. **Replace `YOUR_CLIENT_ID_HERE`** with your actual Client ID from Step 3

---

## 🔵 STEP 5: Update n8n Workflow

The n8n workflow needs to be updated with your credentials. You have two options:

### Option A: Use n8n's Built-in OAuth2 Credential (Recommended)

1. **In n8n UI** (`http://localhost:5678`):
   - Go to **Credentials** → **Add Credential**
   - Search for: `OAuth2 API`
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

2. **Update Workflow** to use this credential instead of hardcoded values

### Option B: Update Workflow JSON (Current Approach)

Update the `Company Onboarding.json` file with your credentials (see next section).

---

## 🔵 STEP 6: Update Company Onboarding Workflow

The workflow JSON file needs your Client ID and Secret. 

**⚠️ SECURITY NOTE**: The workflow currently has hardcoded credentials. After updating, consider using n8n's credential system instead.

**Location**: `Company Onboarding.json`

**Update these lines**:
- Line 48: Replace `client_id` value
- Line 52: Replace `client_secret` value
- Line 28: Update `redirect_uri` to match your setup

---

## 🔵 STEP 7: Verify Configuration

### Test Frontend Connection

1. Start frontend: `cd frontend && npm run dev`
2. Go to: `http://localhost:3000`
3. Login as admin
4. Navigate to **Companies** page
5. Click **Add Company**
6. Enter company name
7. Click **Connect Gmail & Drive**
8. Should redirect to Google OAuth

### Test n8n Workflow

1. Import updated workflow in n8n
2. Activate workflow
3. Test OAuth flow
4. Verify tokens are received

---

## 🔵 STEP 8: Production Considerations

For production deployment:

1. **Update Redirect URIs** in Google Cloud Console:
   - Add your production domain:
     ```
     https://yourdomain.com/rest/oauth2-credential/callback
     https://yourdomain.com/webhook/oauth-callback
     ```

2. **Update Frontend .env**:
   ```env
   VITE_N8N_CALLBACK_URL=https://yourdomain.com/rest/oauth2-credential/callback
   ```

3. **OAuth Consent Screen**:
   - Submit for verification if using sensitive scopes
   - Add production domain to authorized domains

---

## 📝 Summary Checklist

- [ ] Gmail API enabled
- [ ] Google Drive API enabled
- [ ] OAuth consent screen configured
- [ ] OAuth client ID created
- [ ] Redirect URIs added:
  - [ ] `http://localhost:5678/rest/oauth2-credential/callback`
  - [ ] `http://localhost:5678/webhook/oauth-callback`
- [ ] Frontend `.env` file created with `VITE_GOOGLE_CLIENT_ID`
- [ ] n8n workflow updated with credentials
- [ ] Test OAuth flow end-to-end

---

## 🔒 Security Best Practices

1. **Never commit credentials to Git**
   - Add `.env` to `.gitignore`
   - Use environment variables in production

2. **Rotate credentials periodically**
   - Regenerate Client Secret if compromised
   - Update all systems with new credentials

3. **Use n8n Credential System**
   - Store credentials in n8n's encrypted credential store
   - Don't hardcode in workflow JSON

4. **Limit OAuth Scopes**
   - Only request necessary permissions
   - Review and audit regularly

---

## 🐛 Troubleshooting

### "redirect_uri_mismatch" Error
- **Cause**: Redirect URI in Google Console doesn't match the one in your code
- **Fix**: Add exact redirect URI to Google Cloud Console → Credentials → OAuth Client → Authorized redirect URIs

### "invalid_client" Error
- **Cause**: Client ID or Secret is incorrect
- **Fix**: Verify credentials in `.env` and workflow match Google Cloud Console

### "access_denied" Error
- **Cause**: User denied permission or test user not added
- **Fix**: Add user email to OAuth consent screen → Test users

### Refresh Token Not Received
- **Cause**: `access_type=offline` or `prompt=consent` missing
- **Fix**: Ensure OAuth URL includes both parameters (already in frontend code)

---

## 📚 Additional Resources

- [Google OAuth 2.0 Documentation](https://developers.google.com/identity/protocols/oauth2)
- [n8n OAuth2 Credential Guide](https://docs.n8n.io/integrations/credentials/oauth2/)
- [Gmail API Scopes](https://developers.google.com/gmail/api/auth/scopes)
- [Drive API Scopes](https://developers.google.com/drive/api/guides/api-specific-auth)

---

**Last Updated**: 2026-02-04
**Project**: S Combinator Central Agent Platform

