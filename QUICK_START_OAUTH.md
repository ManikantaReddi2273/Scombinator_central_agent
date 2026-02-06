# Quick Start: Google OAuth Setup

## 🚀 Fast Setup (5 Minutes)

### 1. Get Your Credentials from Google Cloud Console

1. Go to: https://console.cloud.google.com/apis/credentials?project=scombinator
2. Click **+ CREATE CREDENTIALS** → **OAuth client ID**
3. Fill in:
   - **Application type**: `Web application`
   - **Name**: `S Combinator n8n OAuth Client`
   - **Authorized redirect URIs**: 
     - `http://localhost:5678/rest/oauth2-credential/callback`
     - `http://localhost:5678/webhook/oauth-callback`
4. Click **CREATE**
5. **COPY** your Client ID and Client Secret immediately!

### 2. Create Frontend .env File

Create file: `frontend/.env`

```env
VITE_API_URL=http://localhost:8000
VITE_GOOGLE_CLIENT_ID=PASTE_YOUR_CLIENT_ID_HERE
VITE_N8N_CALLBACK_URL=http://localhost:5678/rest/oauth2-credential/callback
```

### 3. Update n8n Workflow

Edit `Company Onboarding.json`:
- Line 48: Replace `client_id` value with your Client ID
- Line 52: Replace `client_secret` value with your Client Secret

### 4. Enable APIs

In Google Cloud Console:
- Enable **Gmail API**
- Enable **Google Drive API**

### 5. Test!

1. Start frontend: `cd frontend && npm run dev`
2. Go to http://localhost:3000
3. Login → Companies → Add Company
4. Should redirect to Google OAuth!

---

**For detailed instructions, see:**
- `GOOGLE_OAUTH_SETUP_GUIDE.md` - Complete guide
- `GOOGLE_CLOUD_CONSOLE_STEPS.md` - Step-by-step console instructions

