# Email Ingestion Workflow - Complete Flow Explanation

## Overview
This n8n workflow runs every 5 minutes to check for new emails in all company Gmail inboxes and processes them through the backend API.

## Fixed Issues
1. ✅ **Missing credential_id**: Now properly passed through the workflow
2. ✅ **splitInBatches data access**: Fixed data access pattern for splitInBatches nodes
3. ✅ **Empty company handling**: Added check to skip companies without OAuth credentials
4. ✅ **Backend API structure**: Fixed request body to match backend expectations
5. ✅ **Better error handling**: Added logging and validation at each step

---

## Complete Node-by-Node Flow

### **Node 1: Schedule Trigger**
- **Type**: Schedule Trigger
- **Frequency**: Every 5 minutes
- **Output**: Triggers the workflow automatically
- **Example Output**: `{}` (empty object, just triggers the flow)

---

### **Node 2: Get Companies with OAuth**
- **Type**: HTTP Request
- **Method**: GET
- **URL**: `http://host.docker.internal:8000/api/companies/with-oauth`
- **Purpose**: Fetches all companies that have OAuth connected
- **Example Output**:
```json
[
  {
    "company_id": "550e8400-e29b-41d4-a716-446655440000",
    "name": "AlphaTech",
    "email": "alphatech@gmail.com",
    "n8n_credential_id": "google_cred_123",
    "has_oauth_connected": true,
    "status": "active"
  },
  {
    "company_id": "660e8400-e29b-41d4-a716-446655440001",
    "name": "BetaCorp",
    "email": "betacorp@gmail.com",
    "n8n_credential_id": "google_cred_456",
    "has_oauth_connected": true,
    "status": "active"
  }
]
```

---

### **Node 3: Filter Companies with OAuth**
- **Type**: Code
- **Purpose**: Filters companies to only those with OAuth connected and includes credential_id
- **Code Logic**:
  - Takes all input items
  - Filters where `has_oauth_connected === true`
  - Maps to include: `company_id`, `company_name`, `company_email`, `n8n_credential_id`
  - Returns empty array if no companies found
- **Example Output** (if 2 companies):
```json
[
  {
    "company_id": "550e8400-e29b-41d4-a716-446655440000",
    "company_name": "AlphaTech",
    "company_email": "alphatech@gmail.com",
    "n8n_credential_id": "google_cred_123"
  },
  {
    "company_id": "660e8400-e29b-41d4-a716-446655440001",
    "company_name": "BetaCorp",
    "company_email": "betacorp@gmail.com",
    "n8n_credential_id": "google_cred_456"
  }
]
```

---

### **Node 4: Process Companies One by One**
- **Type**: Split In Batches
- **Batch Size**: 1
- **Purpose**: Processes each company sequentially (one at a time)
- **How it works**:
  - Takes the array from previous node
  - Outputs one company per execution
  - Loops back to process next company after completing current one
- **Example Output** (First iteration):
```json
{
  "company_id": "550e8400-e29b-41d4-a716-446655440000",
  "company_name": "AlphaTech",
  "company_email": "alphatech@gmail.com",
  "n8n_credential_id": "google_cred_123"
}
```

---

### **Node 5: Prepare Token Request**
- **Type**: Code
- **Purpose**: Prepares the URL to get Gmail token for the company
- **Code Logic**:
  - Accesses data from splitInBatches using `$json`
  - Validates `company_id` exists
  - Checks if `n8n_credential_id` exists (returns null if missing)
  - Builds token URL: `http://host.docker.internal:8000/api/companies/{company_id}/gmail-token`
- **Example Output**:
```json
{
  "company_id": "550e8400-e29b-41d4-a716-446655440000",
  "company_name": "AlphaTech",
  "company_email": "alphatech@gmail.com",
  "n8n_credential_id": "google_cred_123",
  "token_url": "http://host.docker.internal:8000/api/companies/550e8400-e29b-41d4-a716-446655440000/gmail-token"
}
```

**Note**: If `n8n_credential_id` is missing, returns `null` and workflow skips to next company.

---

### **Node 6: Has Company Data?**
- **Type**: IF
- **Purpose**: Validates that company data exists before proceeding
- **Condition**: `company_id` is not empty
- **True Path**: Continue to get Gmail token
- **False Path**: Skip to next company (loops back to "Process Companies One by One")

---

### **Node 7: Get Gmail Token from Database**
- **Type**: HTTP Request
- **Method**: GET
- **URL**: `{{ $json.token_url }}` (from previous node)
- **Purpose**: Gets valid Gmail access token from backend (automatically refreshes if expired)
- **Example Output**:
```json
{
  "company_id": "550e8400-e29b-41d4-a716-446655440000",
  "company_email": "alphatech@gmail.com",
  "access_token": "ya29.a0AfH6SMC...",
  "expires_at": "2024-02-05T10:30:00Z"
}
```

---

### **Node 8: Merge Token Data**
- **Type**: Code
- **Purpose**: Merges token data with company data for Gmail API calls
- **Code Logic**:
  - Gets token data from current input (`$json`)
  - Gets company data from "Prepare Token Request" node
  - Combines both into single object
- **Example Output**:
```json
{
  "company_id": "550e8400-e29b-41d4-a716-446655440000",
  "company_name": "AlphaTech",
  "company_email": "alphatech@gmail.com",
  "n8n_credential_id": "google_cred_123",
  "access_token": "ya29.a0AfH6SMC...",
  "expires_at": "2024-02-05T10:30:00Z"
}
```

---

### **Node 9: Check Gmail Inbox via API**
- **Type**: HTTP Request
- **Method**: GET
- **URL**: `https://gmail.googleapis.com/gmail/v1/users/me/messages`
- **Headers**: `Authorization: Bearer {{ $json.access_token }}`
- **Query Parameters**:
  - `q`: `is:unread` (only unread emails)
  - `maxResults`: `10` (max 10 emails per check)
- **Purpose**: Checks Gmail inbox for new unread emails
- **Example Output**:
```json
{
  "messages": [
    {
      "id": "18c1234567890abcdef",
      "threadId": "18c9876543210fedcba"
    },
    {
      "id": "18c0987654321fedcba",
      "threadId": "18c9876543210fedcba"
    }
  ],
  "resultSizeEstimate": 2
}
```

**Note**: If no new emails, `messages` array is empty or missing.

---

### **Node 10: Has New Emails?**
- **Type**: IF
- **Purpose**: Checks if there are new emails to process
- **Condition**: `messages.length > 0`
- **True Path**: Continue to process messages
- **False Path**: Skip to next company (loops back to "Process Companies One by One")

---

### **Node 11: Prepare Message IDs**
- **Type**: Code
- **Purpose**: Prepares data for each message ID to fetch full details
- **Code Logic**:
  - Gets messages array from Gmail API response
  - Gets company data from "Merge Token Data" node
  - Creates array of objects, one per message ID
- **Example Output**:
```json
[
  {
    "company_id": "550e8400-e29b-41d4-a716-446655440000",
    "company_name": "AlphaTech",
    "company_email": "alphatech@gmail.com",
    "n8n_credential_id": "google_cred_123",
    "access_token": "ya29.a0AfH6SMC...",
    "message_id": "18c1234567890abcdef"
  },
  {
    "company_id": "550e8400-e29b-41d4-a716-446655440000",
    "company_name": "AlphaTech",
    "company_email": "alphatech@gmail.com",
    "n8n_credential_id": "google_cred_123",
    "access_token": "ya29.a0AfH6SMC...",
    "message_id": "18c0987654321fedcba"
  }
]
```

---

### **Node 12: Process Messages One by One**
- **Type**: Split In Batches
- **Batch Size**: 1
- **Purpose**: Processes each message sequentially
- **Example Output** (First iteration):
```json
{
  "company_id": "550e8400-e29b-41d4-a716-446655440000",
  "company_name": "AlphaTech",
  "company_email": "alphatech@gmail.com",
  "n8n_credential_id": "google_cred_123",
  "access_token": "ya29.a0AfH6SMC...",
  "message_id": "18c1234567890abcdef"
}
```

---

### **Node 13: Get Full Message Details**
- **Type**: HTTP Request
- **Method**: GET
- **URL**: `https://gmail.googleapis.com/gmail/v1/users/me/messages/{{ $json.message_id }}`
- **Headers**: `Authorization: Bearer {{ $json.access_token }}`
- **Query Parameters**: `format: full` (gets full message with body)
- **Purpose**: Fetches complete email message including body, headers, etc.
- **Example Output**:
```json
{
  "id": "18c1234567890abcdef",
  "threadId": "18c9876543210fedcba",
  "payload": {
    "headers": [
      {"name": "From", "value": "customer@example.com"},
      {"name": "To", "value": "alphatech@gmail.com"},
      {"name": "Subject", "value": "Inquiry about pricing"}
    ],
    "body": {
      "data": "SGVsbG8gV29ybGQ="  // base64 encoded
    }
  }
}
```

---

### **Node 14: Extract Email Data**
- **Type**: Code
- **Purpose**: Extracts email data from Gmail message format and prepares for backend
- **Code Logic**:
  - Extracts headers (From, To, Subject)
  - Decodes base64 body (plain text preferred, HTML fallback)
  - Gets thread_id and message_id
  - Gets company data from "Process Messages One by One" node
  - **IMPORTANT**: Includes `credential_id` for backend mapping
- **Example Output**:
```json
{
  "credential_id": "google_cred_123",
  "company_id": "550e8400-e29b-41d4-a716-446655440000",
  "email_data": {
    "subject": "Inquiry about pricing",
    "body": "Hello, I'm interested in your product pricing...",
    "from": "customer@example.com",
    "to": "alphatech@gmail.com",
    "thread_id": "18c9876543210fedcba",
    "gmail_message_id": "18c1234567890abcdef"
  }
}
```

---

### **Node 15: Process Emails One by One**
- **Type**: Split In Batches
- **Batch Size**: 1
- **Purpose**: Processes each email sequentially before sending to backend
- **Example Output**: Same as Node 14 output

---

### **Node 16: Call Backend API**
- **Type**: HTTP Request
- **Method**: POST
- **URL**: `http://host.docker.internal:8000/api/emails/process`
- **Headers**: `Content-Type: application/json`
- **Body**:
```json
{
  "credential_id": "google_cred_123",
  "email_data": {
    "subject": "Inquiry about pricing",
    "body": "Hello, I'm interested in your product pricing...",
    "from": "customer@example.com",
    "to": "alphatech@gmail.com",
    "thread_id": "18c9876543210fedcba",
    "gmail_message_id": "18c1234567890abcdef"
  }
}
```
- **Purpose**: Sends email to backend for processing (classification, priority scoring, draft generation)
- **Example Response**:
```json
{
  "email_id": "770e8400-e29b-41d4-a716-446655440002",
  "draft_id": "880e8400-e29b-41d4-a716-446655440003",
  "company_id": "550e8400-e29b-41d4-a716-446655440000",
  "status": "processed",
  "classification": {
    "function": "Sales",
    "intent": "Inquiry",
    "urgency": "Can wait",
    "impact": "Revenue",
    "confidence": "Clear"
  },
  "priority_score": "75",
  "executive_summary": "Customer inquiry about product pricing - needs pricing information",
  "recommended_action": "Reply with template"
}
```

---

## Complete Flow Diagram

```
Schedule Trigger (Every 5 min)
    ↓
Get Companies with OAuth
    ↓
Filter Companies with OAuth
    ↓
Process Companies One by One (splitInBatches)
    ↓
Prepare Token Request
    ↓
Has Company Data? (IF)
    ├─ Yes → Get Gmail Token from Database
    └─ No → Loop back to Process Companies
    ↓
Merge Token Data
    ↓
Check Gmail Inbox via API
    ↓
Has New Emails? (IF)
    ├─ Yes → Prepare Message IDs
    └─ No → Loop back to Process Companies
    ↓
Process Messages One by One (splitInBatches)
    ↓
Get Full Message Details
    ↓
Extract Email Data
    ↓
Process Emails One by One (splitInBatches)
    ↓
Call Backend API
    ↓
Loop back to Process Emails (for next email)
    ↓
Loop back to Process Messages (for next message)
    ↓
Loop back to Process Companies (for next company)
```

---

## Backend Processing (What Happens After n8n Calls API)

When the backend receives the email:

1. **Map credential_id to company_id** - Uses `n8n_credential_id` to find company
2. **Duplicate Check** - Checks if `gmail_message_id` already exists
3. **Create Email Record** - Stores email in database
4. **Classification Agent** - Classifies email (Sales/Hiring/Support/etc.)
5. **Priority Scoring** - Calculates priority score (0-100)
6. **Executive Summary** - Generates 1-2 line summary
7. **Action Recommendation** - Recommends action (Reply/Schedule/Hold/etc.)
8. **Draft Generation** - If action = "Reply", generates draft from template
9. **Create Draft Record** - Stores draft in database with status="pending"

---

## UI Flow (What Admin Sees)

1. **Priority Queue Page** (`/priority-queue`)
   - Shows all emails sorted by priority score
   - Displays executive summary, company name, classification
   - Links to drafts if available

2. **Drafts Page** (`/drafts`)
   - Shows pending drafts awaiting approval
   - Admin can:
     - View original email context
     - Edit draft subject/body
     - Approve draft (status → "approved")
     - Reject draft (status → "rejected")

3. **Email Sending** (n8n "Send Approved Drafts" workflow)
   - Runs every 2 minutes
   - Gets approved drafts from backend
   - Sends via Gmail API
   - Updates draft status to "sent"

---

## Key Fixes Applied

1. **Added credential_id tracking**: Now properly passed through entire workflow
2. **Fixed splitInBatches data access**: Changed from `$input.item.json` to `$json`
3. **Added validation**: "Has Company Data?" node skips companies without credential_id
4. **Fixed backend request**: Now sends correct structure: `{credential_id, email_data}`
5. **Better logging**: Added console.log statements for debugging
6. **Error handling**: Workflow continues even if one company fails

---

## Testing the Workflow

### Step 1: Verify Companies Have OAuth
- Check backend: `GET /api/companies/with-oauth`
- Should return companies with `has_oauth_connected: true`

### Step 2: Test Token Retrieval
- Check: `GET /api/companies/{company_id}/gmail-token`
- Should return valid access_token

### Step 3: Test Gmail API Access
- Use the access_token to call Gmail API directly
- Should return list of messages

### Step 4: Test Backend Processing
- Send test email to company inbox
- Wait for workflow to run (or trigger manually)
- Check backend logs for processing
- Check database for new email record
- Check UI for new draft (if action = "Reply")

---

## Troubleshooting

### Issue: Workflow stops at "Prepare Token Request"
- **Check**: Does company have `n8n_credential_id`?
- **Solution**: Reconnect OAuth for the company

### Issue: No emails found
- **Check**: Are there unread emails in Gmail inbox?
- **Check**: Is access_token valid?
- **Solution**: Check Gmail API response in n8n execution logs

### Issue: Backend returns 404
- **Check**: Is `credential_id` being sent correctly?
- **Check**: Does company exist in database?
- **Solution**: Verify credential_id mapping in backend

### Issue: Duplicate emails processed
- **Check**: Is `gmail_message_id` being sent?
- **Solution**: Backend should handle duplicates, but verify the field is included

---

## Next Steps

After this workflow processes emails:
1. Emails appear in Priority Queue UI
2. Drafts appear in Drafts UI (if action = "Reply")
3. Admin reviews and approves drafts
4. "Send Approved Drafts" workflow sends approved emails
5. Replies loop back to this workflow (Flow 1 continues)

