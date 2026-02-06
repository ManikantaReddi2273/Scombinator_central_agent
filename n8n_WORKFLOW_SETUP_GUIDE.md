# n8n "Company Onboarding" Workflow - Step-by-Step Guide

Complete guide to create the workflow that handles Google OAuth and registers companies in your backend.

---

## 📋 Prerequisites

Before starting, ensure you have:
- ✅ n8n running at `http://localhost:5678`
- ✅ Google OAuth credentials configured in n8n (see `n8n_DOCKER_SETUP_GUIDE.md` Step 2)
- ✅ Backend API running at `http://localhost:8000`
- ✅ Backend endpoint `POST /api/companies/register` is working

---

## 🎯 Workflow Overview

**Flow (Two-Part Approach):**

**Part 1: Initiate OAuth**
```
Frontend → n8n Webhook (receives company_name)
→ Redirect to Google OAuth URL
```

**Part 2: Handle OAuth Callback**
```
Google OAuth Callback → n8n Webhook (receives tokens)
→ Extract Tokens Node
→ HTTP Request (calls backend)
→ Redirect to Frontend Success Page
```

**OR Simplified Single Workflow:**
```
Frontend → n8n OAuth URL (with company_name in state)
→ Google OAuth (handled by n8n credential)
→ OAuth Callback Webhook (receives tokens + company_name)
→ Extract Tokens Node
→ HTTP Request (calls backend)
→ Redirect to Frontend
```

**Note:** We'll use the **Simplified Single Workflow** approach, which is cleaner.

---

## 📝 STEP-BY-STEP INSTRUCTIONS

### **STEP 1: Create New Workflow**

1. **Open n8n** in your browser: `http://localhost:5678`
2. **Click** the **"+"** button in the top left (or "Add workflow")
3. **Name the workflow:**
   - Click on "My workflow" at the top
   - Type: `Company Onboarding`
   - Press Enter

---

### **STEP 2: Add Webhook Trigger Node (OAuth Callback)**

This webhook will receive the OAuth callback from Google after authorization.

1. **Click** the **"+"** icon in the center of the canvas (or drag from right sidebar)
2. **Search for:** `webhook`
3. **Select:** "Webhook" node (the one with pink octopus icon)
4. **Configure the Webhook node:**

   **In the "Parameters" tab:**
   
   - **HTTP Method:** Select `GET` from dropdown (OAuth callbacks use GET)
   - **Path:** Type `oauth-callback` (this will be part of the URL)
   - **Authentication:** Leave as `None`
   - **Respond:** Select `When Last Node Finishes` (important!)
   
   **Click "Save"** (top right of node)

5. **Copy the Webhook URL:**
   - You'll see a URL like: `http://localhost:5678/webhook/oauth-callback`
   - **Save this URL** - you'll need to configure it in Google Cloud Console as the redirect URI

---

### **STEP 3: Add Code Node to Extract OAuth Data**

The webhook receives the OAuth callback with authorization code. We need to exchange it for tokens.

1. **Click** the **"+"** icon after the Webhook node
2. **Search for:** `code`
3. **Select:** "Code" node
4. **Connect nodes:** Drag from Webhook output to Code node input

5. **Configure Code node:**

   **In the "Code" tab:**
   
   - **Mode:** Select `Run Once for All Items`
   - **Language:** Select `JavaScript`
   
   **In the code editor, paste this:**

   ```javascript
   // Extract OAuth callback data
   const query = $input.first().json.query || {};
   const code = query.code; // Authorization code from Google
   const state = query.state; // Company name passed in state parameter
   const error = query.error;
   
   if (error) {
     throw new Error(`OAuth error: ${error}`);
   }
   
   if (!code) {
     throw new Error('No authorization code received');
   }
   
   // Return data for next node (OAuth2 API will exchange code for tokens)
   return {
     code: code,
     company_name: state || 'Unknown Company',
     redirect_uri: 'http://localhost:5678/webhook/oauth-callback'
   };
   ```

   **Click "Save"**

**Note:** The actual token exchange will happen in the next node using n8n's OAuth2 credential system.

---

### **STEP 4: Add HTTP Request Node to Exchange Code for Tokens**

We need to manually exchange the authorization code for access/refresh tokens.

1. **Click** the **"+"** icon after the Code node
2. **Search for:** `http request`
3. **Select:** "HTTP Request" node
4. **Connect nodes:** Drag from Code node output to HTTP Request node input

5. **Configure HTTP Request node:**

   **In the "Parameters" tab:**
   
   - **Method:** Select `POST`
   - **URL:** Enter `https://oauth2.googleapis.com/token`
   - **Authentication:** Select `Generic Credential Type` → `Header Auth`
     - **Name:** Leave empty (we'll send in body)
   - **Send Headers:** Toggle ON
     - **Name:** `Content-Type`
     - **Value:** `application/x-www-form-urlencoded`
   
   **In the "Body" section:**
   
   - **Body Content Type:** Select `Form-Data` or `Raw` with `application/x-www-form-urlencoded`
   - **Specify Body:** Toggle ON
   - **Body:** Click Expression mode (</> icon)
   - **Enter:**

   ```javascript
   // Get client_id and client_secret from your Google OAuth credential
   // You'll need to add these as workflow variables or get from credential
   const clientId = 'YOUR_CLIENT_ID'; // Replace with your actual client_id
   const clientSecret = 'YOUR_CLIENT_SECRET'; // Replace with your actual client_secret
   const code = $json.code;
   const redirectUri = $json.redirect_uri;
   
   return `code=${code}&client_id=${clientId}&client_secret=${clientSecret}&redirect_uri=${encodeURIComponent(redirectUri)}&grant_type=authorization_code`;
   ```

   **Click "Save"**

**⚠️ Important:** You need to replace `YOUR_CLIENT_ID` and `YOUR_CLIENT_SECRET` with your actual Google OAuth credentials. For better security, consider storing these in n8n's credential system or environment variables.

---

### **STEP 5: Add Code Node to Extract Tokens from Response**

1. **Click** the **"+"** icon after the HTTP Request node
2. **Search for:** `code`
3. **Select:** "Code" node
4. **Connect nodes:** Drag from HTTP Request output to Code node input

5. **Configure Code node:**

   **In the "Code" tab:**
   
   - **Mode:** Select `Run Once for All Items`
   - **Language:** Select `JavaScript`
   
   **In the code editor, paste this:**

   ```javascript
   // Get token response from previous node
   const tokenResponse = $input.first().json;
   const previousData = $input.first().json.previousData || {};
   
   // Extract tokens
   const accessToken = tokenResponse.access_token;
   const refreshToken = tokenResponse.refresh_token;
   const expiresIn = tokenResponse.expires_in || 3600;
   
   // Get company name from previous step
   const companyName = previousData.company_name || 'Unknown Company';
   
   // Generate a credential ID (you can use n8n's credential ID if available)
   const credentialId = 'google_cred_' + Date.now();
   
   // Get user email (we'll fetch this from Google API in next step, or use a placeholder)
   const email = ''; // Will be set in next step
   
   return {
     company_name: companyName,
     email: email,
     access_token: accessToken,
     refresh_token: refreshToken,
     n8n_credential_id: credentialId,
     expires_in: expiresIn
   };
   ```

   **Click "Save"**

---

### **STEP 6: Add HTTP Request Node to Get User Email (Optional)**

To get the user's email address, we can call Google's userinfo API.

1. **Click** the **"+"** icon after the Code node
2. **Search for:** `http request`
3. **Select:** "HTTP Request" node
4. **Connect nodes:** Drag from Code node output to HTTP Request node input

5. **Configure HTTP Request node:**

   **In the "Parameters" tab:**
   
   - **Method:** Select `GET`
   - **URL:** Enter `https://www.googleapis.com/oauth2/v2/userinfo`
   - **Authentication:** Select `Generic Credential Type` → `Header Auth`
     - **Name:** `Authorization`
     - **Value:** Click Expression mode (</> icon)
     - **Enter:** `Bearer {{ $json.access_token }}`
   
   **Click "Save"**

6. **Add another Code node** to merge email with previous data:

   **Code:**
   ```javascript
   const userInfo = $input.first().json;
   const previousData = $input.first().json.previousData || {};
   
   return {
     ...previousData,
     email: userInfo.email || ''
   };
   ```

---

### **STEP 7: Add HTTP Request Node to Call Backend**

1. **Click** the **"+"** icon after the Code node
2. **Search for:** `http request`
3. **Select:** "HTTP Request" node
4. **Connect nodes:** Drag from Code node output to HTTP Request node input

5. **Configure HTTP Request node:**

   **In the "Parameters" tab:**
   
   - **Method:** Select `POST`
   - **URL:** Enter `http://localhost:8000/api/companies/register`
   - **Authentication:** Leave as `None` (or add if your backend requires it)
   - **Send Headers:** Toggle ON
     - Click "Add Header"
     - **Name:** `Content-Type`
     - **Value:** `application/json`
   
   **In the "Body" section:**
   
   - **Body Content Type:** Select `JSON`
   - **Specify Body:** Toggle ON
   - **Body:** Click the **Expression** mode (</> icon)
   - **Enter this JSON:**

   ```json
   {
     "company_name": "{{ $json.company_name }}",
     "email": "{{ $json.email }}",
     "access_token": "{{ $json.access_token }}",
     "refresh_token": "{{ $json.refresh_token }}",
     "n8n_credential_id": "{{ $json.n8n_credential_id }}"
   }
   ```

   **Click "Save"**

---

### **STEP 8: Add Response Node (Redirect to Frontend)**

This sends a response back to the browser after registration.

1. **Click** the **"+"** icon after the HTTP Request node
2. **Search for:** `respond to webhook`
3. **Select:** "Respond to Webhook" node
4. **Connect nodes:** Drag from HTTP Request output to Respond to Webhook input

5. **Configure Respond to Webhook node:**

   **In the "Parameters" tab:**
   
   - **Respond With:** Select `Redirect`
   - **Response Code:** Select `302` (Temporary Redirect)
   - **Redirect URL:** Click Expression mode (</> icon)
   - **Enter:**

   ```javascript
   // Redirect to frontend success page
   const frontendUrl = 'http://localhost:5173'; // Your frontend URL
   const companyName = $json.company_name || 'Company';
   return `${frontendUrl}/companies?success=true&company=${encodeURIComponent(companyName)}`;
   ```

   **OR if you want JSON response:**

   - **Respond With:** Select `JSON`
   - **Response Code:** Select `200`
   - **Response Body:** Click Expression mode (</> icon)
   - **Enter:**

   ```json
   {
     "success": true,
     "message": "Company registered successfully",
     "company_name": "{{ $json.company_name }}",
     "company_id": "{{ $json.company_id || 'pending' }}"
   }
   ```

   **Click "Save"**

---

### **STEP 9: Configure Google Cloud OAuth Redirect URI**

Before testing, you must configure Google Cloud Console:

1. **Go to Google Cloud Console:** https://console.cloud.google.com/
2. **Navigate to:** APIs & Services → Credentials
3. **Click on your OAuth 2.0 Client ID**
4. **Add Authorized redirect URI:**
   ```
   http://localhost:5678/webhook/oauth-callback
   ```
5. **Click "Save"**

---

### **STEP 10: Create OAuth Initiation Endpoint (Separate Workflow or Backend)**

Since n8n's webhook receives the callback, you need to initiate OAuth from your frontend or backend.

**Option A: Frontend redirects directly to Google OAuth**

Update your frontend to redirect to Google OAuth URL with these parameters:

```javascript
const googleOAuthUrl = `https://accounts.google.com/o/oauth2/v2/auth?` +
  `client_id=YOUR_CLIENT_ID&` +
  `redirect_uri=${encodeURIComponent('http://localhost:5678/webhook/oauth-callback')}&` +
  `response_type=code&` +
  `scope=${encodeURIComponent('https://www.googleapis.com/auth/gmail.readonly https://www.googleapis.com/auth/gmail.send https://www.googleapis.com/auth/drive.readonly https://www.googleapis.com/auth/drive.file')}&` +
  `state=${encodeURIComponent(companyName)}&` +
  `access_type=offline&` +
  `prompt=consent`;
```

**Option B: Create a simple initiation webhook in n8n**

1. Create another workflow: "Initiate Company OAuth"
2. Add Webhook node (POST, path: `initiate-oauth`)
3. Add Code node that generates Google OAuth URL
4. Add Respond to Webhook node that redirects to Google OAuth URL

---

### **STEP 11: Test the Workflow**

1. **Activate the workflow** (toggle switch at top right - should be green)

2. **Test the OAuth flow:**
   - From your frontend, click "Add Company"
   - Enter company name
   - Frontend redirects to Google OAuth URL (with state=company_name)
   - Login with company Gmail account
   - Authorize permissions
   - Google redirects to: `http://localhost:5678/webhook/oauth-callback?code=...&state=...`
   - n8n workflow processes the callback
   - Backend API is called
   - User is redirected back to frontend

3. **Check the workflow execution:**
   - Go to n8n → Executions (left sidebar)
   - You should see execution data
   - Click on execution to see each node's output
   - Verify tokens are extracted and backend is called

---

### **STEP 12: Activate the Workflow**

1. **Click the toggle switch** at the top right of the workflow (next to "Save")
   - It should turn **green** and say "Active"
   - This makes the webhook available for production use

2. **Verify activation:**
   - The webhook URL should now work: `http://localhost:5678/webhook/oauth-callback`
   - The workflow will automatically process OAuth callbacks

---

## 🔄 SIMPLER ALTERNATIVE: Using n8n's Built-in OAuth Flow

If the manual token exchange is too complex, you can use n8n's built-in OAuth credential system:

### **Simplified Workflow:**

1. **Webhook Trigger** (receives OAuth callback with code)
2. **Google OAuth2 API Node** (use "Get Access Token" operation)
   - This automatically exchanges code for tokens using the credential
3. **Extract Tokens** (from OAuth2 API response)
4. **Call Backend**

**To use this approach:**

1. In Google OAuth2 API node:
   - **Operation:** Select `Get Access Token`
   - **Credential:** Select your `S-Combinator Google App` credential
   - **Authorization Code:** `{{ $json.query.code }}`
   - **Redirect URI:** `http://localhost:5678/webhook/oauth-callback`

2. The node will automatically exchange the code for tokens and return them in the response.

3. Extract tokens from the response and proceed to call backend.

**This is simpler but requires the OAuth credential to be properly configured in n8n.**

---

## 🐛 Troubleshooting

### Issue 1: OAuth redirect not working

**Solution:**
- Check that Google OAuth credential is properly configured in n8n
- Verify redirect URI in Google Cloud Console matches n8n's callback URL
- Ensure scopes are correctly set

### Issue 2: Tokens not extracted

**Solution:**
- Check the OAuth2 API node output - tokens might be in a different field
- Modify the Code node to log all data: `console.log($input.all())`
- Check n8n execution logs

### Issue 3: Backend API call fails

**Solution:**
- Verify backend is running: `http://localhost:8000`
- Test backend endpoint directly with Postman
- Check HTTP Request node's error output
- Verify JSON format in request body

### Issue 4: Webhook not receiving data

**Solution:**
- Ensure workflow is activated (toggle is green)
- Check webhook URL is correct
- Verify frontend is sending POST request with correct format
- Check n8n execution logs

---

## ✅ Verification Checklist

After completing all steps, verify:

- [ ] Workflow is created and named "Company Onboarding"
- [ ] Webhook node is configured with path `company-onboarding`
- [ ] Google OAuth2 API node uses correct credential
- [ ] Code node extracts tokens correctly
- [ ] HTTP Request node calls backend API
- [ ] Workflow is activated (green toggle)
- [ ] Webhook URL is accessible: `http://localhost:5678/webhook/company-onboarding`
- [ ] Test execution shows data flowing through all nodes

---

## 🎯 Next Steps

After this workflow is working:

1. **Update Frontend** to use the correct webhook URL
2. **Test full flow:** Frontend → n8n → Google OAuth → Backend
3. **Create "Inbound Email Processing" workflow** (next workflow)
4. **Set up Gmail triggers** for monitoring inboxes

---

## 📚 Additional Resources

- n8n Webhook Documentation: https://docs.n8n.io/integrations/builtin/core-nodes/n8n-nodes-base.webhook/
- n8n OAuth2 API: https://docs.n8n.io/integrations/builtin/credentials/oauth2/
- n8n Code Node: https://docs.n8n.io/integrations/builtin/core-nodes/n8n-nodes-base.code/

---

## 💡 Important Notes

1. **OAuth Flow:** n8n's OAuth2 API node handles the redirect automatically. The user will be redirected to Google, authorize, and then return to n8n.

2. **Token Storage:** n8n stores OAuth tokens in its credential system. We extract them to send to the backend, but n8n also keeps them for future API calls.

3. **Company Name:** The company name is passed from the frontend via the webhook. Make sure the frontend sends it in the request body or query parameter.

4. **Production:** For production, change `localhost` URLs to your actual domain and set up proper HTTPS.

---

**🎉 Once this workflow is complete, you can test the full "Add Company" flow from your frontend!**

---

## 📊 Quick Reference: Node Configuration Summary

### **Node 1: Webhook Trigger**
- **Type:** Webhook
- **Method:** GET
- **Path:** `oauth-callback`
- **Respond:** When Last Node Finishes

### **Node 2: Code (Extract OAuth Code)**
- **Type:** Code
- **Mode:** Run Once for All Items
- **Language:** JavaScript
- **Code:** Extract `code` and `state` from query parameters

### **Node 3: HTTP Request (Exchange Code for Tokens)**
- **Type:** HTTP Request
- **Method:** POST
- **URL:** `https://oauth2.googleapis.com/token`
- **Headers:** `Content-Type: application/x-www-form-urlencoded`
- **Body:** Form data with `code`, `client_id`, `client_secret`, `redirect_uri`, `grant_type`

### **Node 4: Code (Extract Tokens)**
- **Type:** Code
- **Mode:** Run Once for All Items
- **Language:** JavaScript
- **Code:** Extract `access_token`, `refresh_token` from response

### **Node 5: HTTP Request (Get User Email)**
- **Type:** HTTP Request
- **Method:** GET
- **URL:** `https://www.googleapis.com/oauth2/v2/userinfo`
- **Headers:** `Authorization: Bearer {access_token}`

### **Node 6: Code (Merge Email)**
- **Type:** Code
- **Mode:** Run Once for All Items
- **Language:** JavaScript
- **Code:** Merge email with previous data

### **Node 7: HTTP Request (Call Backend)**
- **Type:** HTTP Request
- **Method:** POST
- **URL:** `http://localhost:8000/api/companies/register`
- **Headers:** `Content-Type: application/json`
- **Body:** JSON with `company_name`, `email`, `access_token`, `refresh_token`, `n8n_credential_id`

### **Node 8: Respond to Webhook**
- **Type:** Respond to Webhook
- **Respond With:** Redirect (302) or JSON (200)
- **Redirect URL:** Frontend success page

---

## 🎬 Visual Workflow Flow

```
┌─────────────────┐
│  User clicks    │
│  "Add Company"  │
│  in Frontend    │
└────────┬────────┘
         │
         ▼
┌─────────────────┐
│  Frontend       │
│  redirects to   │
│  Google OAuth   │
│  (with state=   │
│  company_name)  │
└────────┬────────┘
         │
         ▼
┌─────────────────┐
│  Google OAuth   │
│  Login &        │
│  Authorization  │
└────────┬────────┘
         │
         ▼
┌─────────────────┐
│  Google         │
│  redirects to   │
│  n8n webhook:    │
│  /oauth-callback│
│  ?code=...&     │
│  state=...      │
└────────┬────────┘
         │
         ▼
┌─────────────────┐
│  n8n Workflow   │
│  Processes      │
│  Callback       │
└────────┬────────┘
         │
         ├─► Extract code & state
         ├─► Exchange code for tokens
         ├─► Get user email
         ├─► Call Backend API
         └─► Redirect to Frontend
```

---

## 🔑 Key URLs to Remember

- **n8n Webhook (OAuth Callback):** `http://localhost:5678/webhook/oauth-callback`
- **Backend API:** `http://localhost:8000/api/companies/register`
- **Google OAuth Token Endpoint:** `https://oauth2.googleapis.com/token`
- **Google User Info API:** `https://www.googleapis.com/oauth2/v2/userinfo`
- **Frontend URL:** `http://localhost:5173` (or your frontend URL)

---

## ⚠️ Common Mistakes to Avoid

1. **Wrong Redirect URI:** Make sure Google Cloud Console has the exact redirect URI: `http://localhost:5678/webhook/oauth-callback`

2. **Missing State Parameter:** Always pass `company_name` in the `state` parameter when redirecting to Google OAuth

3. **Token Exchange:** Don't forget to include `grant_type=authorization_code` in the token exchange request

4. **Workflow Not Activated:** Make sure the workflow toggle is green (activated) before testing

5. **Wrong Client ID/Secret:** Double-check you're using the correct credentials in the token exchange node

6. **Missing Scopes:** Ensure all required scopes are requested in the initial OAuth redirect

---

## 🚀 Testing Checklist

Before going live, test:

- [ ] Webhook receives OAuth callback correctly
- [ ] Authorization code is extracted from query parameters
- [ ] Token exchange succeeds (check HTTP Request node output)
- [ ] Access token and refresh token are extracted
- [ ] User email is fetched from Google API
- [ ] Backend API receives correct data format
- [ ] Backend successfully creates company record
- [ ] Response redirects user back to frontend
- [ ] Frontend displays success message
- [ ] Company appears in companies list

---

**Need Help?** Check n8n execution logs and node outputs to debug any issues!

