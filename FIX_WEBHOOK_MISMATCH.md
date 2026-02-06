# Fix: Webhook Mismatch - oauth-callback vs oauth-connect

## 🔍 The Problem

Your browser is hitting: `http://localhost:5678/webhook/oauth-callback`
But your active workflow "Company OAuth Connection" uses: `oauth-connect`

This means the webhook request goes to the wrong endpoint, so no workflow executes.

---

## ✅ Solution: Two Options

### Option 1: Use oauth-connect (Recommended for connecting to existing companies)

Since you're connecting OAuth to an **existing company**, you should use `oauth-connect`.

**Step 1: Check your frontend `.env` file**

1. Go to `frontend` folder
2. Check if you have a `.env` file
3. If it exists, open it and check `VITE_N8N_CALLBACK_URL`
4. **It should be**: `VITE_N8N_CALLBACK_URL=http://localhost:5678/webhook/oauth-connect`
5. If it's set to `oauth-callback`, **change it to `oauth-connect`**
6. **Save the file**
7. **Restart your frontend dev server** (stop and start again)

**Step 2: Verify "Company OAuth Connection" workflow is active**

1. In n8n, go to "Company OAuth Connection" workflow
2. Make sure it's **Published** (green dot)
3. Check the Webhook node path is `oauth-connect`

---

### Option 2: Activate "Company Onboarding" workflow (for oauth-callback)

If you want to use `oauth-callback` instead:

**Step 1: Activate "Company Onboarding" workflow**

1. In n8n, go to **Workflows**
2. Find **"Company Onboarding"** workflow
3. **Open it**
4. **Activate it** (toggle ON in top-right)
5. **Save** (Ctrl+S)

**Step 2: Keep environment variable as oauth-callback**

- Make sure `VITE_N8N_CALLBACK_URL=http://localhost:5678/webhook/oauth-callback`

---

## 🎯 Recommended: Use oauth-connect

Since you're using the **two-step registration** approach:
- **Step 1**: Create company (no OAuth) ✅ Already working
- **Step 2**: Connect OAuth to existing company → Should use `oauth-connect`

**So use Option 1** - change your environment variable to `oauth-connect`.

---

## 📋 Quick Fix Steps

1. **Check `frontend/.env` file**:
   ```env
   VITE_N8N_CALLBACK_URL=http://localhost:5678/webhook/oauth-connect
   ```

2. **If no `.env` file exists**, create one:
   ```bash
   cd frontend
   # Create .env file with:
   VITE_N8N_CALLBACK_URL=http://localhost:5678/webhook/oauth-connect
   VITE_GOOGLE_CLIENT_ID=407115728261-22odd5dsa5grrtmdqena19bs5id0l0a5.apps.googleusercontent.com
   ```

3. **Restart frontend**:
   - Stop the dev server (Ctrl+C)
   - Start again: `npm run dev`

4. **Test again**:
   - Go to Companies page
   - Click "Connect Gmail & Drive"
   - Should now redirect to `oauth-connect` endpoint
   - Should trigger "Company OAuth Connection" workflow

---

## 🔍 How to Verify

After fixing, when you click "Connect Gmail & Drive":

1. **Check browser URL** after Google redirect:
   - Should be: `http://localhost:5678/webhook/oauth-connect?code=...`
   - NOT: `http://localhost:5678/webhook/oauth-callback?code=...`

2. **Check n8n Executions**:
   - Go to "Company OAuth Connection" workflow
   - Click "Executions" tab
   - Should see execution logs

---

## 🐛 Still Not Working?

If you've changed the environment variable but it's still using `oauth-callback`:

1. **Clear browser cache** (Ctrl+Shift+Delete)
2. **Hard refresh** the frontend page (Ctrl+F5)
3. **Restart frontend dev server** completely
4. **Check browser console** (F12) for any errors

