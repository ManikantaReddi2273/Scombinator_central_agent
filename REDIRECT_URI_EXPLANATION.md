# Redirect URI Explanation - n8n vs Workflow

## 🔍 Understanding the Two Redirect URIs

You have **TWO different redirect URIs** for **TWO different purposes**. This is **CORRECT** and **OK**!

---

## 📍 Redirect URI #1: n8n Credential System

**URI**: `http://localhost:5678/rest/oauth2-credential/callback`

**Where it's used:**
- In your **n8n Credential** configuration (the "Google account" credential you see in n8n)
- This is for n8n's **built-in OAuth2 credential system**
- Used when you want n8n to automatically handle OAuth flows

**Current Status:**
- ✅ Configured in n8n credential
- ✅ Added to Google Cloud Console
- ❌ **NOT used in your current workflow** (you're using webhook approach instead)

---

## 📍 Redirect URI #2: Workflow Webhook

**URI**: `http://localhost:5678/webhook/oauth-callback`

**Where it's used:**
- In your **Company Onboarding workflow** (the webhook node)
- In your **frontend** (`AddCompanyModal.tsx`)
- This is for your **custom workflow** that processes OAuth manually

**Current Status:**
- ✅ Configured in frontend
- ✅ Configured in workflow
- ✅ Added to Google Cloud Console
- ✅ **This is what your workflow uses**

---

## ✅ Is Having Both OK?

**YES! It's perfectly fine to have both redirect URIs in Google Cloud Console.**

**Why?**
1. **Flexibility**: You can use either approach (credential system or webhook)
2. **No conflicts**: Google allows multiple redirect URIs for the same OAuth client
3. **Future-proof**: If you want to switch to n8n's credential system later, it's already configured

**Your Google Cloud Console should have BOTH:**
- ✅ `http://localhost:5678/rest/oauth2-credential/callback` (for n8n credential system)
- ✅ `http://localhost:5678/webhook/oauth-callback` (for your workflow)

---

## 🎯 Which One is Actually Used?

**In your current setup:**

1. **Frontend** → Uses: `http://localhost:5678/webhook/oauth-callback`
2. **Workflow Webhook** → Receives at: `http://localhost:5678/webhook/oauth-callback`
3. **Workflow HTTP Request** → Uses: `http://localhost:5678/webhook/oauth-callback` (for token exchange)

**So your workflow uses the WEBHOOK redirect URI, not the credential one.**

---

## 🔧 What About the n8n Credential?

The n8n credential with redirect_uri `http://localhost:5678/rest/oauth2-credential/callback` is:
- ✅ **Configured correctly** (no need to change it)
- ✅ **Not causing any issues** (it's just sitting there, unused)
- ✅ **Available for future use** (if you want to switch to credential-based OAuth)

**You can:**
- **Option A**: Leave it as is (recommended - keeps options open)
- **Option B**: Delete it if you're sure you'll never use n8n's credential system

---

## 📊 Current Flow (What Actually Happens)

```
1. Frontend
   └─> Redirects to Google OAuth
       └─> redirect_uri: http://localhost:5678/webhook/oauth-callback ✅

2. Google OAuth
   └─> User authorizes
       └─> Redirects to: http://localhost:5678/webhook/oauth-callback?code=XXX ✅

3. n8n Webhook
   └─> Receives callback at /webhook/oauth-callback ✅
       └─> Triggers workflow

4. Workflow HTTP Request
   └─> Exchanges code for tokens
       └─> Uses redirect_uri: http://localhost:5678/webhook/oauth-callback ✅
```

**The n8n credential redirect_uri is NOT in this flow!**

---

## ✅ Summary

| Redirect URI | Used In | Currently Active? |
|--------------|---------|-------------------|
| `http://localhost:5678/rest/oauth2-credential/callback` | n8n Credential | ❌ No (not used in workflow) |
| `http://localhost:5678/webhook/oauth-callback` | Workflow + Frontend | ✅ Yes (this is what you're using) |

**Both are in Google Cloud Console** ✅ **This is correct and OK!**

---

## 🎯 What You Should Do

**Nothing! Everything is configured correctly:**

1. ✅ Both redirect URIs are in Google Cloud Console
2. ✅ Frontend uses the webhook redirect_uri
3. ✅ Workflow uses the webhook redirect_uri
4. ✅ n8n credential is configured (but not used - that's fine)

**You can:**
- **Keep both redirect URIs** in Google Cloud Console (recommended)
- **Keep the n8n credential** as is (it's not causing any issues)
- **Test your workflow** - it should work now!

---

## 🚀 Next Steps

1. **Re-import the updated workflow** in n8n (if you haven't already)
2. **Test the OAuth flow** from the frontend
3. **Verify it works** - the redirect_uri_mismatch error should be gone!

**Everything is set up correctly. You're good to go!** ✅

