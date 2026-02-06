

# ✅ SYSTEM PRINCIPLE (Foundation)

Before anything:

* There is **ONE S-Combinator Google App**

  * Has `client_id` + `client_secret`
* These are configured **once in n8n**
* n8n uses this app to connect **many company accounts**
* Each company connection generates **separate tokens**
* Every table in DB uses `company_id`

So:

> One App → Many Companies → Fully Isolated Data

---

# 📝 PLAN UPDATES (Key Changes from Original)

**🔄 This plan has been updated with recommended improvements:**

1. **Token Storage:** Backend now stores encrypted tokens (not just credential_id reference)
   - Enables direct Google API access
   - Better control over token lifecycle
   - Automatic token refresh

2. **OAuth Flow:** n8n automatically calls backend after OAuth completes
   - No manual credential_id transfer needed
   - Automatic company registration
   - Seamless onboarding

3. **Drive Access:** Backend calls Google Drive API directly
   - No dependency on n8n for file access
   - Faster response times
   - Better error handling

4. **Token Management:** Complete token lifecycle in backend
   - Encryption at rest
   - Automatic refresh
   - Secure storage

**All changes are clearly marked with 🔄 throughout this document.**

---

# 🏗️ CORE DATABASE RULE (MANDATORY)

Every major table must include:

```
company_id
```

Example:

```
companies
emails
drafts
candidates
templates
logs
approvals
policies
```

All queries must filter by `company_id`.

This guarantees isolation.

---

# 🚀 COMPLETE FLOW: “ADD COMPANY” (END TO END)

This is the main flow you will implement.

---

## 🔵 STEP 0 — One-Time Platform Setup (Only Once)

### (You do this before launching)

1. Create Google Cloud Project
2. Enable:

   * Gmail API
   * Drive API
3. Create OAuth App
4. Get:

   * client_id
   * client_secret
5. Add these in n8n → Google OAuth Credentials

After this → Never touch again.

---

## 🔵 STEP 1 — Admin Login

### In Your Backend

You hardcode:

```
ADMIN_EMAIL
ADMIN_PASSWORD
```

Flow:

```
Admin → Login Page → Backend Check → Dashboard
```

No signup.

Only admin.

---

## 🔵 STEP 2 — Admin Clicks “Add Company”

UI shows:

```
Company Name: [________]

[ Connect Gmail & Drive ]
```

Admin enters:

```
AlphaTech
```

Clicks button.

---

## 🔵 STEP 3 — Redirect to n8n OAuth

Your backend redirects browser to:

```
n8n OAuth Authorization URL
```

Example:

```
https://n8n.yourdomain.com/oauth2/google
```

Now control moves to n8n.

---

## 🔵 STEP 4 — n8n Talks to Google (Using client_id)

Behind the scenes:

n8n sends:

```
client_id + scopes
```

To Google.

Google knows:

“This is S-Combinator App.”

---

## 🔵 STEP 5 — Company Gmail Login

Google shows login screen.

Admin logs in as:

```
alphatech@gmail.com
```

(Company email, not admin email)

---

## 🔵 STEP 6 — Permission Screen

Google asks:

> Allow S-Combinator App to:
>
> * Read Gmail
> * Send Gmail
> * Access Drive

Admin clicks:

✅ Allow

---

## 🔵 STEP 7 — Google Issues Tokens

Google sends to n8n:

```
access_token
refresh_token
```

These belong ONLY to:

```
alphatech@gmail.com
```

n8n stores securely as credential.

---

## 🔵 STEP 8 — n8n Calls Backend with Tokens

**🔄 UPDATED APPROACH:**

After n8n stores the credential, n8n workflow automatically calls backend:

```
n8n HTTP Node → POST to Backend:
POST /api/companies/register

{
  "company_name": "AlphaTech",
  "email": "alphatech@gmail.com",
  "access_token": "...",
  "refresh_token": "...",
  "n8n_credential_id": "google_cred_101"
}
```

**Why this approach:**
- Backend needs tokens to call Google APIs directly
- Backend stores tokens encrypted for security
- n8n keeps credential for workflow triggers
- Both systems have what they need

---

## 🔵 STEP 9 — Backend Creates Company Record

**🔄 UPDATED APPROACH:**

Backend receives tokens from n8n.

Backend:

1. **Generates company_id:**
   ```
   company_id = SC-001
   ```

2. **Encrypts tokens** (using AES/KMS):
   ```
   encrypted_access_token = encrypt(access_token)
   encrypted_refresh_token = encrypt(refresh_token)
   ```

3. **Saves to database:**
   ```
   companies table
   -----------------
   company_id: SC-001
   name: AlphaTech
   email: alphatech@gmail.com
   encrypted_access_token: [encrypted]
   encrypted_refresh_token: [encrypted]
   access_token_expires_at: [timestamp]
   n8n_credential_id: google_cred_101 (reference only)
   status: active
   created_at: [timestamp]
   ```

**Key Changes:**
- ✅ Backend stores tokens (encrypted) for direct Google API access
- ✅ Backend can refresh tokens when expired
- ✅ n8n credential_id stored as reference (for mapping)
- ✅ Complete token lifecycle management in backend

Company is now registered.

---

# 🔁 SAME PROCESS FOR ALL COMPANIES

Second company:

```
betasoft@gmail.com
→ google_cred_102
→ SC-002
```

Third company:

```
gamma@gmail.com
→ google_cred_103
→ SC-003
```

Database:

| company_id | name      | email                | n8n_credential_id | status |
| ---------- | --------- | -------------------- | ---------------- | ------ |
| SC-001     | AlphaTech | alphatech@gmail.com  | google_cred_101   | active |
| SC-002     | BetaSoft  | betasoft@gmail.com   | google_cred_102   | active |
| SC-003     | GammaCorp | gamma@gmail.com      | google_cred_103   | active |

**Note:** Tokens are stored encrypted in separate columns (not shown in table above for security).

---

# 📩 AUTOMATION FLOW (AFTER COMPANY IS ADDED)

Once company is connected → automation runs 24/7.

---

## 🟢 STEP A — n8n Watches Inbox

n8n workflow:

```
Gmail Trigger (credential)
```

Example:

```
Watch inbox using google_cred_101
```

Runs every few minutes (or webhook).

---

## 🟢 STEP B — New Email Arrives

Mail sent to:

```
alphatech@gmail.com
```

n8n detects using:

```
google_cred_101
```

---

## 🟢 STEP C — n8n Sends to Backend

n8n → Backend:

```
{
  subject,
  body,
  from,
  credential_id: google_cred_101
}
```

---

## 🟢 STEP D — Backend Maps to Company

**🔄 UPDATED APPROACH:**

Backend receives `credential_id` from n8n.

Backend queries database:

```sql
SELECT company_id, name, encrypted_access_token, encrypted_refresh_token
FROM companies
WHERE n8n_credential_id = 'google_cred_101'
```

Result:

```
company_id = SC-001
name = AlphaTech
```

**Alternative mapping (if credential_id not available):**
- Backend can also map by email address:
  ```sql
  SELECT company_id FROM companies WHERE email = 'alphatech@gmail.com'
  ```

Everything now runs inside AlphaTech context.

---

## 🟢 STEP E — Load Company Drive Policies

**🔄 UPDATED APPROACH:**

Backend calls Google Drive API **directly** (not through n8n):

```
Backend Process:
1. Decrypt access_token for SC-001
2. Check if token expired → Refresh if needed
3. Call Google Drive API directly:
   GET https://www.googleapis.com/drive/v3/files
   Authorization: Bearer {access_token}
   Query: folder path = /AlphaTech/policies
4. Fetch files:
   - /AlphaTech/policies/brand_tone.txt
   - /AlphaTech/policies/pricing_rules.pdf
   - /AlphaTech/templates/email_template_1.txt
   - /AlphaTech/templates/faq.json
```

AI loads:

* Brand tone
* Pricing rules
* Templates
* FAQs

**Why this approach:**
- ✅ Backend has direct control over token refresh
- ✅ No dependency on n8n for file access
- ✅ Faster response times
- ✅ Better error handling
- ✅ Backend can cache policies locally

---

## 🟢 STEP F — AI Processing

Backend AI does (per your blueprint):

1. Classify
2. Score priority
3. Summarize
4. Recommend action
5. Generate draft



Saved as:

```
emails(company_id=SC-001)
drafts(company_id=SC-001)
```

---

## 🟢 STEP G — Dashboard Review

UI queries:

```
SELECT * FROM drafts WHERE company_id = SC-001
```

Admin sees:

```
AlphaTech → Pricing Inquiry → Draft Ready
```

---

## 🟢 STEP H — Admin Approves

Admin clicks:

✅ Approve & Send

Backend updates:

```
status = approved
```

---

## 🟢 STEP I — n8n Sends Email

n8n uses:

```
google_cred_101
```

Calls Gmail API.

Reply sent from:

```
alphatech@gmail.com
```

---

## 🟢 STEP J — Logging

Backend writes:

```
logs(company_id=SC-001)
```

Includes:

* Source
* Template
* Approval
* Timestamp

Audit ready.

---

# 🔐 WHY EMAILS & DRIVES NEVER MIX

Because:

| Company | n8n Credential | Backend Tokens | Gmail/Drive Used |
| ------- | -------------- | -------------- | --------------- |
| Alpha   | google_cred_101 | SC-001 tokens  | Alpha only      |
| Beta    | google_cred_102 | SC-002 tokens  | Beta only       |
| Gamma   | google_cred_103 | SC-003 tokens  | Gamma only      |

**Isolation Guarantees:**
- n8n never crosses credentials in workflows
- Backend tokens are company-specific (stored with company_id)
- Each company's data is completely isolated in database
- No token leakage between companies

---

# 🔧 KEY ARCHITECTURAL DECISIONS (Why These Changes)

## Decision 1: Backend Stores Tokens (Not Just credential_id)

**Why:**
- ✅ Backend needs direct Google API access for Drive files
- ✅ Better control over token refresh lifecycle
- ✅ No dependency on n8n for file access (faster, more reliable)
- ✅ Backend can cache policies locally
- ✅ Better error handling and retry logic

**How:**
- Tokens encrypted at rest (AES-256 or KMS)
- Automatic refresh when expired
- Secure storage in database

## Decision 2: n8n Also Keeps Credentials

**Why:**
- ✅ n8n needs credentials for Gmail triggers
- ✅ n8n needs credentials for sending emails
- ✅ Workflow orchestration requires n8n to have access
- ✅ Separation of concerns: n8n = orchestration, Backend = intelligence

**How:**
- n8n stores credentials internally (its own system)
- Backend stores tokens separately (for API calls)
- Both reference the same company via mapping

## Decision 3: n8n Calls Backend After OAuth

**Why:**
- ✅ Backend needs tokens immediately after OAuth
- ✅ No manual step required
- ✅ Automatic company registration
- ✅ Single source of truth (backend database)

**How:**
- n8n workflow includes HTTP node after OAuth
- Calls POST /api/companies/register
- Backend validates and stores

## Decision 4: Backend Calls Google APIs Directly

**Why:**
- ✅ Faster response times (no n8n dependency)
- ✅ Better error handling
- ✅ Direct control over API calls
- ✅ Can implement caching
- ✅ Easier to debug and monitor

**How:**
- Backend uses Google API client libraries
- Authenticates with stored tokens
- Refreshes tokens automatically when needed

## Token Refresh Flow

**When Backend Needs to Access Drive:**

1. Backend checks `access_token_expires_at` in database
2. If expired (or expiring soon):
   - Decrypt `refresh_token`
   - Call Google OAuth API: `POST /oauth2/v4/token`
   - Get new `access_token`
   - Encrypt and save new token
   - Update `access_token_expires_at`
3. Use new token for API call

**Automatic Process:**
- Happens transparently before every Drive API call
- No manual intervention needed
- Handles token expiration gracefully

---

# 📐 ARCHITECTURE MAPPING (From Your Document)

This matches exactly:

### Layer 1: Companies

* Gmail
* Drive

### Layer 2: n8n

* Triggers
* Orchestration

### Layer 3: Your Code

* Policy
* AI
* Logic

### Layer 4: DB

* All with company_id

### Layer 5: UI

* Review

### Layer 6: Send

* Gmail API



---

# 📋 IMPLEMENTATION CHECKLIST (For Cursor)

Give this to Cursor:

---

## 1️⃣ Auth Module

* Hardcode admin credentials
* JWT session
* No signup

---

## 2️⃣ Company Onboarding

**🔄 UPDATED APPROACH:**

* POST /company/create (initiates flow)
* Redirect to n8n OAuth URL
* n8n handles OAuth → stores credential
* n8n workflow calls: POST /api/companies/register
  - Receives: company_name, email, access_token, refresh_token, n8n_credential_id
* Backend:
  - Generates company_id (UUID format: SC-001)
  - Encrypts tokens (AES/KMS)
  - Saves to companies table
  - Returns success to n8n
* n8n completes workflow

---

## 3️⃣ Database

**🔄 UPDATED APPROACH:**

### Companies Table (Example Schema)

```sql
CREATE TABLE companies (
    company_id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    name VARCHAR(255) NOT NULL,
    email VARCHAR(255) NOT NULL UNIQUE,
    
    -- Encrypted tokens (stored as TEXT/BLOB)
    encrypted_access_token TEXT NOT NULL,
    encrypted_refresh_token TEXT NOT NULL,
    access_token_expires_at TIMESTAMP,
    
    -- n8n reference (for mapping)
    n8n_credential_id VARCHAR(255),
    
    -- Status
    status VARCHAR(50) DEFAULT 'active',
    created_at TIMESTAMP DEFAULT NOW(),
    updated_at TIMESTAMP DEFAULT NOW()
);
```

### All Other Tables Must Include:

```
company_id UUID (Foreign Key → companies.company_id)
```

**Mandatory for:**
- emails
- drafts
- candidates
- templates
- logs
- approvals
- policies (cached)

**All queries must filter by company_id for isolation.**

---

## 4️⃣ n8n Workflows

### Workflow 1: Company Onboarding (OAuth Callback)

**🔄 NEW WORKFLOW:**

```
Google OAuth Trigger
→ Store Credential (n8n internal)
→ Extract: access_token, refresh_token, credential_id
→ HTTP Node: POST /api/companies/register
  {
    "company_name": "...",
    "email": "...",
    "access_token": "...",
    "refresh_token": "...",
    "n8n_credential_id": "..."
  }
→ Wait for Backend Response
→ Complete Registration
```

### Workflow 2: Inbound Email Processing

```
Gmail Trigger (using credential_id)
→ HTTP Node: POST /api/emails/process
  {
    "credential_id": "google_cred_101",
    "email_data": {...}
  }
→ Wait for Backend Processing
→ (Backend saves draft, waits for approval)
→ Poll Backend: GET /api/drafts/{draft_id}/status
→ If approved: Send Email (using credential_id)
→ If rejected: Log and notify
```

### Workflow 3: Drive File Change Sync (Optional)

```
Drive Trigger (file changed in company folder)
→ HTTP Node: POST /api/policies/sync
  {
    "credential_id": "google_cred_101",
    "file_path": "/AlphaTech/policies/brand_tone.txt"
  }
→ Backend fetches file directly (using stored tokens)
→ Backend updates cache
```

**Note:** Drive sync can also be handled by backend polling or webhooks.

---

## 5️⃣ Backend Services

**🔄 UPDATED APPROACH:**

* **Token Manager Service**
  - Encrypt/decrypt tokens
  - Refresh expired tokens (Google OAuth refresh)
  - Token lifecycle management
  
* **Tenant Service**
  - Map credential_id → company_id
  - Map email → company_id
  - Company context management

* **Google API Client Service**
  - Direct Google Drive API calls
  - Direct Gmail API calls (if needed)
  - Handles authentication with stored tokens
  - Automatic token refresh

* **Policy Loader Service**
  - Fetches policies from Drive (using Google API Client)
  - Caches policies locally
  - Updates cache when Drive files change

* **AI Engine (LangGraph)**
  - Classification
  - Priority scoring
  - Summarization
  - Draft generation
  - Uses policies from Policy Loader

* **Template Engine**
  - Loads templates from Drive
  - Applies brand tone
  - Variable substitution

* **Audit Logger**
  - Logs all actions with company_id
  - Tracks token usage
  - Records AI decisions

---

## 6️⃣ UI

* Company Filter
* Priority Queue
* Draft Editor
* Hiring Pipeline

---

# 🧠 FINAL ONE-PARAGRAPH SUMMARY

**🔄 UPDATED VERSION:**

> When the admin clicks Add Company, the system redirects to n8n's Google OAuth using S-Combinator's single client_id. The company's Gmail logs in and authorizes access. Google gives tokens to n8n, which stores them as a credential for workflow triggers. n8n then automatically calls the backend API with the tokens. The backend encrypts and stores these tokens, generates a unique company_id, and saves the mapping (including n8n_credential_id for reference). From then on, n8n watches that inbox using its stored credential and sends new emails to the backend. The backend uses its stored tokens to directly call Google Drive API and load company-specific policies, templates, and brand guidelines. The backend runs AI logic (LangGraph) with company context, saves all data with company_id, and shows results in the dashboard. After admin approval, n8n sends emails using its credential. Because each company has separate tokens stored in both n8n (for workflows) and backend (for API calls), their Gmail and Drive never mix, and the backend has full control over token refresh and Google API access.

---

