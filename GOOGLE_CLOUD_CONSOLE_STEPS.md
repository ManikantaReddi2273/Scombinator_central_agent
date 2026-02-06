# Detailed Google Cloud Console Steps

## Step-by-Step Instructions for Google Cloud Console

Follow these exact steps in your Google Cloud Console at: https://console.cloud.google.com/welcome?project=scombinator

---

## 1. Enable APIs

### Enable Gmail API:
1. Click on **☰ Menu** (top left)
2. Go to **APIs & Services** → **Library**
3. In the search bar, type: `Gmail API`
4. Click on **Gmail API** from results
5. Click the blue **ENABLE** button
6. Wait for confirmation

### Enable Google Drive API:
1. Still in **APIs & Services** → **Library**
2. In the search bar, type: `Google Drive API`
3. Click on **Google Drive API** from results
4. Click the blue **ENABLE** button
5. Wait for confirmation

---

## 2. Configure OAuth Consent Screen

1. Go to **APIs & Services** → **OAuth consent screen**
2. You'll see a form with these fields:

   **App Information:**
   - **App name**: `S Combinator Central Agent Platform`
   - **User support email**: Select `reddimanikanta2005@gmail.com` from dropdown
   - **App logo**: (Optional - skip for now)
   - **App domain**: (Optional - skip for now)
   - **Application home page**: (Optional - skip for now)
   - **Privacy policy link**: (Optional - skip for now)
   - **Terms of service link**: (Optional - skip for now)
   - **Authorized domains**: (Optional - skip for now)
   - **Developer contact information**: `reddimanikanta2005@gmail.com`

3. Click **SAVE AND CONTINUE**

4. **Scopes** (Step 2):
   - Click **ADD OR REMOVE SCOPES**
   - In the filter box, search and add these scopes one by one:
     - `https://www.googleapis.com/auth/gmail.readonly`
     - `https://www.googleapis.com/auth/gmail.send`
     - `https://www.googleapis.com/auth/drive.readonly`
     - `https://www.googleapis.com/auth/drive.file`
   - Click **UPDATE** button
   - Click **SAVE AND CONTINUE**

5. **Test users** (Step 3):
   - Click **+ ADD USERS**
   - Enter: `reddimanikanta2005@gmail.com`
   - Click **ADD**
   - Click **SAVE AND CONTINUE**

6. **Summary** (Step 4):
   - Review your settings
   - Click **BACK TO DASHBOARD**

---

## 3. Create OAuth 2.0 Client ID

1. Go to **APIs & Services** → **Credentials**
2. At the top, click **+ CREATE CREDENTIALS**
3. Select **OAuth client ID** from dropdown

4. **OAuth client creation** form:
   - **Application type**: Select `Web application`
   - **Name**: `S Combinator n8n OAuth Client`

   - **Authorized JavaScript origins**:
     Click **+ ADD URI** and add:
     - `http://localhost:5678`
     - `http://localhost:3000`
   
   - **Authorized redirect URIs**:
     Click **+ ADD URI** and add these TWO URIs (one at a time):
     ```
     http://localhost:5678/rest/oauth2-credential/callback
     ```
     Then click **+ ADD URI** again and add:
     ```
     http://localhost:5678/webhook/oauth-callback
     ```

5. Click **CREATE**

6. **IMPORTANT - Copy Your Credentials**:
   A popup will appear showing:
   - **Your Client ID**: `XXXXXXXXXX-XXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXX.apps.googleusercontent.com`
   - **Your Client secret**: `GOCSPX-XXXXXXXXXXXXXXXXXXXXXXXXX`
   
   **⚠️ COPY THESE NOW!** You won't see the secret again.
   
   - Copy Client ID to a safe place
   - Copy Client Secret to a safe place
   - Click **OK**

---

## 4. Where to Put Your Credentials

### A. Frontend (.env file)

Create file: `frontend/.env`

```env
VITE_API_URL=http://localhost:8000
VITE_GOOGLE_CLIENT_ID=YOUR_CLIENT_ID_HERE.apps.googleusercontent.com
VITE_N8N_CALLBACK_URL=http://localhost:5678/rest/oauth2-credential/callback
```

Replace `YOUR_CLIENT_ID_HERE` with your actual Client ID.

### B. n8n Workflow (Company Onboarding.json)

Update these lines in `Company Onboarding.json`:

**Line 48** (client_id):
```json
"value": "YOUR_CLIENT_ID_HERE.apps.googleusercontent.com"
```

**Line 52** (client_secret):
```json
"value": "GOCSPX-YOUR_CLIENT_SECRET_HERE"
```

### C. n8n Credential System (Alternative - Recommended)

Instead of hardcoding in workflow, use n8n's credential system:

1. Open n8n: http://localhost:5678
2. Go to **Credentials** (left sidebar)
3. Click **+ Add Credential**
4. Search for: `OAuth2 API`
5. Fill in:
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
6. Click **Save**

---

## 5. Verify Your Setup

### Check Redirect URIs Match:

1. In Google Cloud Console → **Credentials**
2. Click on your OAuth 2.0 Client ID
3. Verify **Authorized redirect URIs** contains:
   - ✅ `http://localhost:5678/rest/oauth2-credential/callback`
   - ✅ `http://localhost:5678/webhook/oauth-callback`

### Test the Flow:

1. Start your frontend: `cd frontend && npm run dev`
2. Go to: http://localhost:3000
3. Login as admin
4. Go to **Companies** page
5. Click **Add Company**
6. Enter a company name
7. Click **Connect Gmail & Drive**
8. You should be redirected to Google OAuth login

---

## Common Issues & Solutions

### Issue: "redirect_uri_mismatch"
**Solution**: 
- Make sure the redirect URI in Google Console **exactly matches** the one in your code
- Check for trailing slashes, http vs https, port numbers
- Both URIs must be added to Google Console

### Issue: "invalid_client"
**Solution**:
- Verify Client ID and Secret are correct
- Check for extra spaces when copying
- Make sure you're using the correct credentials (not from a different project)

### Issue: "access_denied"
**Solution**:
- Make sure `reddimanikanta2005@gmail.com` is added to **Test users** in OAuth consent screen
- Check that all required scopes are added

### Issue: No refresh token received
**Solution**:
- Ensure OAuth URL includes `access_type=offline`
- Ensure OAuth URL includes `prompt=consent`
- Both are already in the frontend code

---

## Security Reminders

1. **Never commit `.env` files to Git**
2. **Never share your Client Secret publicly**
3. **Regenerate credentials if compromised**
4. **Use environment variables in production**

---

**Need Help?** Check the main guide: `GOOGLE_OAUTH_SETUP_GUIDE.md`

