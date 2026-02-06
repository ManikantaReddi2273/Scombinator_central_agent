# Fix: "No Executions Found" in n8n

## 🎯 The Problem

You've imported the workflow, but no executions appear when OAuth callback happens.

## ✅ The Solution (Most Common Issue)

**The workflow is NOT actually active in n8n UI, even though the JSON file says `"active": true`.**

When you import a workflow JSON file, n8n does NOT automatically activate it. You must manually activate it in the UI.

---

## 📋 Step-by-Step Fix

### Step 1: Open n8n and Find the Workflow

1. Open: `http://localhost:5678`
2. Click **"Workflows"** in the left sidebar
3. Find **"Company OAuth Connection"** in the list
4. **Click on it** to open the workflow

---

### Step 2: Activate the Workflow

1. **Look at the top-right corner** of the workflow editor
2. You should see a **toggle switch** or **"Active"** button
3. **If it's OFF (gray/inactive)**:
   - **Click the toggle** to turn it **ON (green/active)**
4. You should see:
   - ✅ Green indicator
   - ✅ "Active" text
   - ✅ Toggle switch in ON position

---

### Step 3: Save the Workflow

1. **Press `Ctrl+S`** (or click the **Save** button in top-right)
2. Wait for "Workflow saved" confirmation
3. **Important**: The workflow must be saved after activating

---

### Step 4: Verify Webhook is Registered

1. **Click on the Webhook node** (first node in the workflow)
2. **Look at the bottom** of the node configuration
3. You should see a **Webhook URL** like:
   ```
   http://localhost:5678/webhook/oauth-connect
   ```
4. **Copy this URL** - it should match what's in your frontend

---

### Step 5: Test It

1. Go to your frontend: `http://localhost:3000/companies`
2. Click **"Connect Gmail & Drive"** on any company
3. Authorize in Google
4. **Go back to n8n**
5. Click the **"Executions"** tab (in the workflow or in left sidebar)
6. **You should now see execution logs!**

---

## 🔍 If Still Not Working

### Check 1: Multiple Workflows

You might have TWO workflows:
- "Company Onboarding" (old, uses `oauth-callback`)
- "Company OAuth Connection" (new, uses `oauth-connect`)

**Make sure ONLY "Company OAuth Connection" is active.**

---

### Check 2: Webhook Path Mismatch

1. In n8n, check the Webhook node path: `oauth-connect`
2. In frontend (`Companies.tsx`), check the redirect URI
3. In Google Cloud Console, check the redirect URI
4. **All three must match**: `http://localhost:5678/webhook/oauth-connect`

---

### Check 3: Test Webhook Directly

Open this URL in a new browser tab:
```
http://localhost:5678/webhook/oauth-connect?code=test&state=test-id
```

**Expected Results**:
- ✅ **If workflow is active**: You'll see an execution in n8n (even if it fails)
- ❌ **If workflow is NOT active**: 404 error or "webhook not found"

---

### Check 4: n8n Container Status

1. Open terminal
2. Run:
   ```bash
   cd n8n
   docker-compose ps
   ```
3. Make sure n8n container is **running** (Status: "Up")

---

## 🎯 Quick Visual Guide

```
n8n Workflow Editor:
┌─────────────────────────────────────┐
│  Company OAuth Connection    [ON]  │ ← Toggle must be ON (green)
│                                     │
│  [Webhook] → [Code] → [HTTP] ...   │
│                                     │
│  Webhook URL:                       │
│  http://localhost:5678/            │
│  webhook/oauth-connect              │
└─────────────────────────────────────┘
```

---

## ✅ Success Indicators

When it's working, you'll see:

1. ✅ **Toggle is ON** (green) in workflow editor
2. ✅ **Executions appear** in "Executions" tab
3. ✅ **Webhook URL** is visible in Webhook node
4. ✅ **No 404 errors** when testing webhook URL directly

---

## 🚨 Most Common Mistake

**"I imported the workflow, so it should be active."**

❌ **WRONG**: Importing doesn't activate it.

✅ **CORRECT**: You must manually click the toggle to activate it.

---

## 📞 Still Need Help?

If you've done all the above and it's still not working:

1. **Take a screenshot** of:
   - The workflow editor showing the toggle switch
   - The Webhook node configuration
   - The Executions tab (showing "No executions found")

2. **Check n8n logs**:
   ```bash
   cd n8n
   docker-compose logs n8n | tail -50
   ```

3. **Verify the exact webhook URL** shown in n8n matches your frontend and Google Cloud Console.

