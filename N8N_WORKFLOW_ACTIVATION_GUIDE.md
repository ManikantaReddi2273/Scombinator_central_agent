# n8n Workflow Activation Guide - Fix "No Executions Found"

## 🔍 Problem
When you click "Connect Gmail & Drive", the OAuth callback reaches n8n but no workflow executions appear. This means the workflow is not active or the webhook isn't registered.

---

## ✅ Solution: Activate the Workflow in n8n

### Step 1: Import the Workflow (if not already imported)

1. **Open n8n**: Go to `http://localhost:5678`
2. **Click "Workflows"** in the left sidebar
3. **Click "Import from File"** (or the "+" button → "Import from File")
4. **Select**: `Company OAuth Connection.json` from your project folder
5. **Click "Import"**

---

### Step 2: Verify the Workflow is Active

1. **Open the workflow** "Company OAuth Connection" in n8n
2. **Check the top-right corner** - you should see a toggle switch
3. **Make sure it's ON (green/active)**
   - If it's OFF (gray), **click it to activate**
4. **You should see**: "Active" or "Published" status

---

### Step 3: Verify Webhook Configuration

1. **Click on the "Webhook" node** (first node in the workflow)
2. **Check the "Parameters" tab**:
   - **Path**: Should be `oauth-connect`
   - **HTTP Method**: Should be `GET` (or `POST` - both work for OAuth callbacks)
3. **Copy the Webhook URL** shown at the bottom:
   - Should be: `http://localhost:5678/webhook/oauth-connect`
4. **Click "Save"** on the webhook node

---

### Step 4: Add Redirect URI to Google Cloud Console

The frontend uses `http://localhost:5678/webhook/oauth-connect`, but this might not be in Google Cloud Console.

1. **Go to Google Cloud Console**: https://console.cloud.google.com/
2. **Navigate to**: APIs & Services → Credentials
3. **Click on your OAuth 2.0 Client ID** (the one with Client ID: `407115728261-22odd5dsa5grrtmdqena19bs5id0l0a5`)
4. **Scroll to "Authorized redirect URIs"**
5. **Click "+ ADD URI"**
6. **Add this URI**:
   ```
   http://localhost:5678/webhook/oauth-connect
   ```
7. **Click "SAVE"**

**Your Google Cloud Console should now have ALL THREE redirect URIs:**
- ✅ `http://localhost:5678/rest/oauth2-credential/callback` (for n8n credential system)
- ✅ `http://localhost:5678/webhook/oauth-callback` (for old Company Onboarding workflow)
- ✅ `http://localhost:5678/webhook/oauth-connect` (for new Company OAuth Connection workflow) ← **NEW**

---

### Step 5: Test the Workflow

1. **Go to your frontend**: `http://localhost:3000`
2. **Login as admin**
3. **Go to Companies page**
4. **Click "Connect Gmail & Drive"** on any company
5. **Authorize in Google**
6. **Check n8n**:
   - Go to the "Company OAuth Connection" workflow
   - Click the **"Executions"** tab
   - You should now see execution logs!

---

## 🐛 Troubleshooting

### Issue: Still "No executions found"

**Check 1: Workflow is Active**
- In n8n, open the workflow
- Top-right corner should show "Active" (green toggle ON)
- If not, click the toggle to activate

**Check 2: Webhook URL Matches**
- Frontend uses: `http://localhost:5678/webhook/oauth-connect`
- n8n webhook path: `oauth-connect`
- Google Console has: `http://localhost:5678/webhook/oauth-connect`
- All three must match!

**Check 3: n8n is Running**
- Open: `http://localhost:5678`
- If it doesn't load, start n8n:
  ```bash
  cd n8n
  docker-compose up -d
  ```

**Check 4: Check n8n Logs**
- In terminal, run:
  ```bash
  cd n8n
  docker-compose logs -f n8n
  ```
- Try connecting OAuth again
- Look for errors in the logs

**Check 5: Webhook Node Settings**
- Open the Webhook node in n8n
- Make sure "Response Mode" is set to "When Last Node Finishes" or "Response Node"
- Make sure there's a "Respond to Webhook" node at the end of the workflow

---

## 📋 Quick Checklist

- [ ] Workflow "Company OAuth Connection" is imported in n8n
- [ ] Workflow is **Active** (toggle ON in top-right)
- [ ] Webhook path is `oauth-connect`
- [ ] Redirect URI `http://localhost:5678/webhook/oauth-connect` is in Google Cloud Console
- [ ] Frontend `.env` has `VITE_N8N_CALLBACK_URL=http://localhost:5678/webhook/oauth-connect`
- [ ] n8n is running (`http://localhost:5678` loads)
- [ ] Test OAuth connection and check Executions tab

---

## 🎯 Expected Flow

```
1. User clicks "Connect Gmail & Drive" in frontend
   ↓
2. Frontend redirects to Google OAuth
   ↓
3. User authorizes in Google
   ↓
4. Google redirects to: http://localhost:5678/webhook/oauth-connect?code=XXX&state=company_id
   ↓
5. n8n Webhook node receives the callback
   ↓
6. Workflow executes (you should see it in Executions tab)
   ↓
7. Workflow exchanges code for tokens
   ↓
8. Workflow calls backend to connect OAuth
   ↓
9. Workflow redirects back to frontend
```

---

## ✅ Success Indicators

When it's working, you should see:
- ✅ Executions appear in n8n "Executions" tab
- ✅ Company shows "OAuth Connected" in frontend
- ✅ No errors in n8n execution logs
- ✅ Backend receives OAuth tokens successfully

