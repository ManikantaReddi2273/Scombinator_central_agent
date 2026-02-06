# n8n Webhook Diagnostic - Why No Executions Appear

## 🔍 Common Causes

### Issue 1: Workflow Not Actually Active in n8n UI

**Problem**: The JSON file says `"active": true`, but n8n UI might not have it activated.

**Solution**:
1. Open n8n: `http://localhost:5678`
2. Go to **Workflows** → Find "Company OAuth Connection"
3. **Check the toggle switch** in the top-right corner
   - If it's **OFF (gray)**, click it to turn it **ON (green)**
4. **Save the workflow** (Ctrl+S or click Save button)

**Important**: Importing a JSON file doesn't automatically activate the workflow. You must manually activate it in the UI.

---

### Issue 2: Webhook Path Mismatch

**Problem**: The webhook path in n8n doesn't match what Google is calling.

**Check**:
1. In n8n, open the "Company OAuth Connection" workflow
2. Click on the **Webhook node** (first node)
3. Look at the **"Path"** field - should be: `oauth-connect`
4. Look at the **Webhook URL** shown below - should be: `http://localhost:5678/webhook/oauth-connect`
5. **Compare with frontend**: Check `frontend/src/pages/Companies.tsx` line 22
   - Should use: `http://localhost:5678/webhook/oauth-connect`

**If mismatch**:
- Update the webhook path in n8n to match
- OR update frontend to match n8n
- Make sure Google Cloud Console has the correct redirect URI

---

### Issue 3: Webhook Not Registered

**Problem**: n8n hasn't registered the webhook endpoint.

**Check**:
1. Open n8n: `http://localhost:5678`
2. Go to **Settings** (gear icon) → **Webhooks**
3. Look for webhook: `oauth-connect`
4. If it's not there, the workflow isn't active

**Solution**:
1. Make sure workflow is **Active** (toggle ON)
2. **Save the workflow**
3. Wait a few seconds for n8n to register the webhook
4. Refresh the webhooks page

---

### Issue 4: Wrong Workflow is Active

**Problem**: You have multiple workflows and the wrong one is active.

**Check**:
1. In n8n, go to **Workflows**
2. Look for these workflows:
   - "Company Onboarding" (old workflow, uses `oauth-callback`)
   - "Company OAuth Connection" (new workflow, uses `oauth-connect`)
3. **Only "Company OAuth Connection" should be active**
4. Deactivate "Company Onboarding" if it's active

---

### Issue 5: n8n Not Receiving the Request

**Problem**: The OAuth callback isn't reaching n8n.

**Test**:
1. Open browser console (F12)
2. Try connecting OAuth
3. Check the Network tab
4. Look for request to `localhost:5678/webhook/oauth-connect`
5. Check the response status code

**If 404**:
- Webhook not registered
- Workflow not active
- Wrong path

**If 200 but no execution**:
- Workflow might be failing immediately
- Check n8n logs

---

## 🔧 Step-by-Step Fix

### Step 1: Verify Workflow is Active

1. Open n8n: `http://localhost:5678`
2. Click **Workflows** in left sidebar
3. Find **"Company OAuth Connection"**
4. **Click on it** to open
5. **Look at top-right corner**:
   - Should see a **toggle switch**
   - If it's **OFF (gray)**, click it to turn **ON (green)**
   - Should say **"Active"** or show green indicator
6. **Press Ctrl+S** to save (or click Save button)

---

### Step 2: Verify Webhook Configuration

1. **In the workflow**, click on the **Webhook node** (first node)
2. **Check "Parameters" tab**:
   - **Path**: `oauth-connect`
   - **HTTP Method**: `GET` (or `POST`)
   - **Response Mode**: `When Last Node Finishes` or `Response Node`
3. **Look at the Webhook URL** shown:
   - Should be: `http://localhost:5678/webhook/oauth-connect`
4. **Click "Save"** on the webhook node

---

### Step 3: Test Webhook Directly

Open a new browser tab and go to:
```
http://localhost:5678/webhook/oauth-connect?code=test123&state=test-company-id
```

**Expected**:
- If workflow is active: Should see execution in n8n
- If workflow not active: 404 error or "webhook not found"

---

### Step 4: Check n8n Logs

1. Open terminal
2. Run:
   ```bash
   cd n8n
   docker-compose logs -f n8n
   ```
3. Try connecting OAuth again
4. Watch the logs for:
   - Webhook requests
   - Errors
   - Execution starts

---

### Step 5: Verify Google Cloud Console

1. Go to: https://console.cloud.google.com/apis/credentials?project=scombinator
2. Click your OAuth 2.0 Client ID
3. Check **"Authorized redirect URIs"**:
   - Should have: `http://localhost:5678/webhook/oauth-connect`
4. If missing, **add it** and **save**

---

## 🎯 Quick Diagnostic Checklist

Run through this checklist:

- [ ] n8n is running (`http://localhost:5678` loads)
- [ ] Workflow "Company OAuth Connection" exists in n8n
- [ ] Workflow is **Active** (toggle ON, green indicator)
- [ ] Workflow is **Saved** (Ctrl+S)
- [ ] Webhook node path is `oauth-connect`
- [ ] Webhook URL shown is `http://localhost:5678/webhook/oauth-connect`
- [ ] Frontend uses `http://localhost:5678/webhook/oauth-connect`
- [ ] Google Cloud Console has `http://localhost:5678/webhook/oauth-connect`
- [ ] Test webhook URL directly in browser
- [ ] Check n8n logs for errors

---

## 🐛 Still Not Working?

If you've checked everything above and it's still not working:

1. **Deactivate the workflow** (toggle OFF)
2. **Save the workflow**
3. **Wait 5 seconds**
4. **Activate the workflow** (toggle ON)
5. **Save the workflow**
6. **Wait 5 seconds** for webhook to register
7. **Try OAuth connection again**

If still not working, check:
- n8n version compatibility
- Docker container status
- Network/firewall blocking localhost:5678
- Browser console for errors

