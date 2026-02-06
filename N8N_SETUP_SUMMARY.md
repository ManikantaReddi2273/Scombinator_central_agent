# n8n Setup Summary - Quick Reference

This is a quick summary of what needs to be done to complete the n8n workflow setup.

---

## ✅ Completed Steps

1. ✅ n8n Docker container is running
2. ✅ n8n is accessible at `http://localhost:5678`
3. ✅ Frontend "Add Company" button is implemented
4. ✅ Backend API endpoint `/api/companies/register` exists

---

## 🔧 Remaining Steps (In Order)

### **STEP 1: Set Up Google Cloud OAuth App** ⚠️ REQUIRED

**Time:** ~10 minutes

1. Go to: https://console.cloud.google.com/
2. Create/Select Project
3. Enable APIs:
   - Gmail API
   - Google Drive API
4. Create OAuth 2.0 Credentials:
   - APIs & Services → Credentials → Create Credentials → OAuth client ID
   - Application type: Web application
   - Authorized redirect URIs: `http://localhost:5678/webhook/oauth-callback`
   - Save `client_id` and `client_secret`

**Save these values - you'll need them next!**

---

### **STEP 2: Configure Google OAuth in n8n** ⚠️ REQUIRED

**Time:** ~5 minutes

1. Open n8n: `http://localhost:5678`
2. Go to: Settings → Credentials → Add Credential
3. Search: "Google OAuth2 API"
4. Fill in:
   - **Credential Name:** `S-Combinator Google App`
   - **Client ID:** [from Step 1]
   - **Client Secret:** [from Step 1]
   - **Scopes:**
     ```
     https://www.googleapis.com/auth/gmail.readonly
     https://www.googleapis.com/auth/gmail.send
     https://www.googleapis.com/auth/drive.readonly
     https://www.googleapis.com/auth/drive.file
     ```
5. Click "Save"

---

### **STEP 3: Create n8n Workflow** ⚠️ REQUIRED

**Time:** ~20 minutes

Follow the detailed guide: **`n8n_WORKFLOW_SETUP_GUIDE.md`**

**Quick Summary:**
1. Create workflow: "Company Onboarding"
2. Add nodes:
   - Webhook (GET, path: `oauth-callback`)
   - Code (extract OAuth code)
   - HTTP Request (exchange code for tokens)
   - Code (extract tokens)
   - HTTP Request (get user email)
   - HTTP Request (call backend API)
   - Respond to Webhook (redirect to frontend)
3. Activate workflow

---

### **STEP 4: Configure Frontend Environment Variables** ⚠️ REQUIRED

**Time:** ~2 minutes

Create/update `frontend/.env`:

```env
VITE_GOOGLE_CLIENT_ID=your_client_id_here
VITE_N8N_CALLBACK_URL=http://localhost:5678/webhook/oauth-callback
```

**Restart frontend** after adding these variables.

---

### **STEP 5: Test the Complete Flow** ✅ VERIFY

**Time:** ~5 minutes

1. Open frontend: `http://localhost:5173`
2. Login as admin
3. Click "Add Company"
4. Enter company name (e.g., "TestCompany")
5. Click "Connect Gmail & Drive"
6. Should redirect to Google OAuth
7. Login with company Gmail account
8. Authorize permissions
9. Should redirect back to frontend
10. Company should appear in companies list

---

## 📋 Configuration Checklist

Before testing, verify:

- [ ] Google Cloud OAuth app created
- [ ] Redirect URI configured: `http://localhost:5678/webhook/oauth-callback`
- [ ] Google OAuth credential added in n8n
- [ ] n8n workflow "Company Onboarding" created
- [ ] n8n workflow is activated (green toggle)
- [ ] Frontend `.env` has `VITE_GOOGLE_CLIENT_ID`
- [ ] Backend is running at `http://localhost:8000`
- [ ] Frontend is running at `http://localhost:5173`
- [ ] n8n is running at `http://localhost:5678`

---

## 🔗 Important URLs

- **n8n:** http://localhost:5678
- **n8n OAuth Callback:** http://localhost:5678/webhook/oauth-callback
- **Backend API:** http://localhost:8000
- **Backend Register Endpoint:** http://localhost:8000/api/companies/register
- **Frontend:** http://localhost:5173
- **Google OAuth:** https://accounts.google.com/o/oauth2/v2/auth

---

## 🐛 Troubleshooting

### Issue: "OAuth redirect_uri_mismatch"

**Solution:** 
- Check Google Cloud Console → Credentials → OAuth 2.0 Client ID
- Ensure redirect URI exactly matches: `http://localhost:5678/webhook/oauth-callback`
- No trailing slashes!

### Issue: "Workflow not receiving callback"

**Solution:**
- Verify workflow is activated (green toggle)
- Check webhook path is exactly `oauth-callback`
- Test webhook URL directly in browser

### Issue: "Tokens not extracted"

**Solution:**
- Check n8n execution logs
- Verify Code node is extracting correct fields
- Check HTTP Request node output for token response

### Issue: "Backend API call fails"

**Solution:**
- Verify backend is running
- Test endpoint with Postman
- Check request body format matches backend expectations
- Check backend logs for errors

---

## 📚 Documentation Files

- **Detailed Workflow Guide:** `n8n_WORKFLOW_SETUP_GUIDE.md`
- **Docker Setup Guide:** `n8n_DOCKER_SETUP_GUIDE.md`
- **Project Plan:** `our_plan_now.md`

---

## 🎯 Next Steps After Setup

Once the workflow is working:

1. **Create "Inbound Email Processing" workflow**
   - Gmail trigger
   - Process emails
   - Call backend API

2. **Implement LangGraph AI agents** (backend)
   - Email classification
   - Priority scoring
   - Draft generation

3. **Test end-to-end flow**
   - Add company
   - Send test email
   - Verify AI processing
   - Check dashboard

---

## 💡 Quick Tips

1. **Always activate workflows** before testing (green toggle)
2. **Check n8n executions** to debug issues
3. **Use n8n's test mode** to test individual nodes
4. **Save workflow frequently** while building
5. **Check node outputs** to verify data flow

---

**🎉 Once all steps are complete, your "Add Company" flow will work end-to-end!**

