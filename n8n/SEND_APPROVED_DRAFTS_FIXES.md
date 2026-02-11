# Send Approved Drafts Workflow - Fixes Applied

## Issues Fixed

### 1. **Data Access in "Get Email Info" Node**
**Problem:** Used `$('Get Draft Details').item.json.email_id` which doesn't work correctly in `splitInBatches` mode.

**Fix:** Changed to use `$json.email_id` from the current item (which comes from "Merge Draft & Company" node that has `draft_email_id`).

**Location:** Line 158
```javascript
// Before:
url: "=http://host.docker.internal:8000/api/emails/{{ $('Get Draft Details').item.json.email_id }}"

// After:
url: "=http://host.docker.internal:8000/api/emails/{{ $json.draft_email_id }}"
```

### 2. **Data Access in "Prepare Email Message" Node**
**Problem:** Used `$('Get Draft Details').item.json`, `$('Get Company Info').item.json`, and `$('Get Email Info').item.json` which doesn't work reliably in batch processing.

**Fix:** 
- Added new "Merge Draft & Company" node to combine draft and company data
- Updated "Prepare Email Message" to use `$json` for email data and `$('Merge Draft & Company').item.json` for merged draft/company data
- Added proper mode: `runOnceForEachItem`
- Added extensive validation and logging

**Location:** Lines 141-154 (new node), Lines 179-191 (updated node)

### 3. **Data Access in "Mark Draft as Sent" Node**
**Problem:** Used `$('Get Draft Details').item.json.id` which doesn't work correctly.

**Fix:** Changed to use `$json.draft_id` from "Prepare Email Message" output.

**Location:** Line 222
```javascript
// Before:
url: "=http://host.docker.internal:8000/api/drafts/{{ $('Get Draft Details').item.json.id }}/sent"

// After:
url: "=http://host.docker.internal:8000/api/drafts/{{ $json.draft_id }}/sent"
```

### 4. **Added "Merge Draft & Company" Node**
**Purpose:** Combines draft data from "Get Draft Details" with company data from "Get Company Info" to ensure all required fields are available downstream.

**Features:**
- Validates draft_id and email_id are present
- Validates n8n_credential_id is present (required for Gmail API)
- Adds extensive logging for debugging
- Uses `runOnceForEachItem` mode

**Location:** Lines 141-154

### 5. **Improved Error Handling**
- Added timeout of 30 seconds to all HTTP requests (was 10 seconds for "Mark Draft as Sent")
- Added validation in "Prepare Email Message" node
- Added console logging throughout for debugging

### 6. **Workflow Activation**
**Fix:** Changed `"active": false` to `"active": true` so the workflow will run automatically.

**Location:** Line 364

## Updated Workflow Flow

1. **Schedule Trigger** → Runs every 2 minutes
2. **Get Approved Drafts** → Fetches approved drafts from backend
3. **Has Approved Drafts?** → Checks if array length > 0
4. **Process Drafts One by One** → `splitInBatches` with batchSize=1
5. **Get Draft Details** → Gets full draft data
6. **Get Company Info** → Gets company data with `n8n_credential_id`
7. **Merge Draft & Company** → **NEW NODE** - Combines draft and company data
8. **Get Email Info** → Gets original email data (uses `draft_email_id` from merged data)
9. **Prepare Email Message** → Prepares email for Gmail API (uses merged data)
10. **Send Email via Gmail** → Sends email using n8n Gmail node
11. **Mark Draft as Sent** → Updates draft status to "sent" (uses `draft_id` from prepared data)
12. **Error Handler** → Catches any errors

## Data Flow

```
Get Approved Drafts
  → [{id, company_id, email_id, ...}]

Process Drafts One by One
  → {id, company_id, email_id, ...}

Get Draft Details
  → {id, company_id, email_id, subject, body, ...}

Get Company Info
  → {company_id, name, email, n8n_credential_id, ...}

Merge Draft & Company
  → {
      draft_id, draft_subject, draft_body, draft_email_id,
      company_id, company_name, n8n_credential_id
    }

Get Email Info
  → {id, from_email, thread_id, ...}

Prepare Email Message
  → {
      draft_id, company_id, n8n_credential_id,
      to, subject, body, thread_id, raw_message
    }

Send Email via Gmail
  → (sends email)

Mark Draft as Sent
  → {draft_id, status: "sent", ...}
```

## Testing Checklist

- [ ] Workflow is active in n8n
- [ ] Approved drafts are fetched correctly
- [ ] Draft details are retrieved
- [ ] Company info is retrieved with credential ID
- [ ] Draft and company data are merged correctly
- [ ] Email info is retrieved
- [ ] Email message is prepared correctly
- [ ] Gmail API sends email successfully
- [ ] Draft status is updated to "sent"
- [ ] Error handling works if any step fails

## Notes

- The workflow processes drafts one at a time (batchSize=1) to avoid overwhelming the Gmail API
- All HTTP requests have 30-second timeouts
- Extensive logging is added for debugging
- The workflow will automatically loop back to process the next draft after marking one as sent

