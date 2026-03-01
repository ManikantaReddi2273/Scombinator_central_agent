# n8n Workflows for Flow 2 (B2B & B2C Outbound Email)

This document describes the n8n workflows needed for Flow 2 (B2B and B2C Outbound Email) functionality.

## Prerequisites

- n8n instance running and accessible
- Backend API running at `http://localhost:8000` (or configured URL)
- Company OAuth tokens stored in backend database
- Gmail API credentials configured in n8n

### Authentication for "Update CRM After Send" (and other backend calls)

The **Update CRM After Send** node calls `POST /api/outbound/sent/{draft_id}/update-crm`, which accepts either:

1. **X-API-Key (recommended for n8n)**  
   - In backend `.env`, set: `N8N_SERVICE_API_KEY=your-secret-key`  
   - In n8n, set the same value as an environment variable: `N8N_SERVICE_API_KEY`  
   - The workflow sends header `X-API-Key: {{ $env.N8N_SERVICE_API_KEY }}`.  
   - Use a long-lived secret (e.g. 32+ random characters).

2. **Bearer JWT**  
   - Use the same admin JWT as for "Get Approved Drafts" / "Mark Draft as Sent".  
   - In the node, set **Authentication** to **Generic Credential Type** → **Header Auth** with `Authorization: Bearer <your-jwt>` (or use a credential that provides the token).  
   - If you use Bearer, you can remove the `X-API-Key` header from the node.

## Workflow 1: Poll Approved Drafts and Send

**Purpose:** Polls for approved outbound drafts every 5 minutes, sends them via Gmail API, and updates CRM sheets.

**Trigger:** Schedule (Cron) - Runs every 5 minutes

**Steps:**

1. **Schedule Trigger**
   - Type: Cron
   - Cron Expression: `*/5 * * * *` (every 5 minutes)
   - Timezone: Your timezone

2. **HTTP Request: Get Approved Drafts**
   - Method: GET
   - URL: `http://localhost:8000/api/drafts/approved`
   - Query Parameters:
     - `limit`: 10
   - Headers:
     - `Authorization`: `Bearer {n8n_service_token}` (if using service token)
     - OR use Basic Auth if configured
   - Response: Array of approved drafts

3. **Split In Batches** (Optional - for processing multiple drafts)
   - Batch Size: 1
   - This processes each draft individually

4. **For Each Draft:**
   
   a. **HTTP Request: Get Company Gmail Token**
      - Method: GET
      - URL: `http://localhost:8000/api/companies/{company_id}/gmail-token`
      - Path Parameters:
        - `company_id`: `{{ $json.company_id }}`
      - Headers:
        - `Authorization`: `Bearer {n8n_service_token}`
      - Response: `{ "access_token": "..." }`
   
   b. **Gmail API: Send Email**
      - Action: Send Email
      - Credentials: Use access_token from previous step
      - From: `{{ $json.from_email }}`
      - To: `{{ $json.to_email }}`
      - Subject: `{{ $json.subject }}`
      - Body: `{{ $json.body }}`
      - Format: Plain Text
      - Response: Gmail message ID
   
   c. **HTTP Request: Mark Draft as Sent**
      - Method: POST
      - URL: `http://localhost:8000/api/drafts/{{ $json.draft_id }}/sent`
      - Headers:
        - `Authorization`: `Bearer {n8n_service_token}`
      - Body: Empty or `{}`
      - Response: Success confirmation
   
   d. **HTTP Request: Update CRM** (run after Mark Draft as Sent)
      - Method: POST
      - URL: `http://localhost:8000/api/outbound/sent/{{ $json.draft_id }}/update-crm`
      - Headers (use one of):
        - `X-API-Key`: `{{ $env.N8N_SERVICE_API_KEY }}` (set `N8N_SERVICE_API_KEY` in backend .env and in n8n env)
        - OR `Authorization`: `Bearer {n8n_service_token}` (admin JWT)
      - Body (minimum; include `lead_source` for B2C so backend updates B2C_FUNNEL; all other fields optional or derived from playbook):
        ```json
        {
          "lead_id": "{{ $('Get Email Info').item.json.recipient_context.lead_id }}",
          "lead_source": "{{ $('Get Email Info').item.json.recipient_context.lead_source || '' }}",
          "activity_summary": "Sent email: {{ $json.subject }}"
        }
        ```
      - Optional body fields (override backend defaults): `stage`, `engagement_level`, `owner`, `status`, `objection_notes`, `notes`, `next_followup_date`.
      - Backend behavior (same for **B2B** and **B2C** outbound):
        - **lead_id** and **lead_source** are taken from the draft’s `email.recipient_context` when not provided in the request body, so B2C updates work even if the node sends an empty body.
        - **B2B**: Updates **LEADS** (Stage e.g. "Email Sent", Last_Activity_Date, Next_Followup_Date from PLAYBOOKS.md or default 3 days, Status "Active"), **ACTIVITIES** (one row linked by `lead_id`), **TASKS** (follow-up task linked by `lead_id`). For time_based (follow-up) sends, **Follow_Up_Count** is incremented.
        - **B2C**: Updates **B2C_FUNNEL** (Stage "Email Sent", Last_Activity_Date, Next_Followup_Date, Status "Active"), **ACTIVITIES** and **TASKS** using B2C_Lead_ID as `lead_id`. **Follow_Up_Count** is incremented for time_based follow-up sends, same logic as B2B.
      - Response: CRM update confirmation

5. **Error Handling**
   - Add error handling nodes to catch and log failures
   - Send notification (Slack/Email) if workflow fails

**Configuration Notes:**
- Store n8n service token as n8n credential or environment variable
- Handle rate limiting (Gmail API has quotas)
- Add retry logic for transient failures
- Log all sent emails for audit

---

## Workflow 1b: B2C Follow-Up Drafts (same logic as B2B)

**Purpose:** Same behaviour as B2B Follow-Up Drafts but for B2C leads. Runs **every 24 hours**. When **Next_Followup_Date** (in CRM) equals **today** (backend uses app date, e.g. IST):

- **Follow_Up_Count &lt; 2:** create **one** follow-up draft → draft goes to **human-in-the-loop** (approval in app). When the human approves and **Send Approved Drafts** sends the email, the backend **increments Follow_Up_Count** in B2C_FUNNEL (via Update CRM After Send). So the count increases **only when the email is sent**, not when the draft is created.
- **Follow_Up_Count ≥ 2:** do **not** create another draft; instead update CRM as **"No Response – Outreach Stopped"** (PATCH mark-outreach-stopped).

So: first time due → create draft → human sends → count becomes 1. Second time due → create draft → human sends → count becomes 2. Third time due → mark "No Response" and stop.

**File:** `n8n/B2C Follow-Up Drafts.json`

**Steps (mirror B2B):**
1. **Schedule Trigger:** every **24 hours** (same as B2B).
2. Get companies with OAuth → filter `has_oauth_connected`.
3. For each company: GET `/api/outbound/b2c/leads-due-for-follow-up?company_id=...` (X-API-Key). Backend returns `leads_due_for_draft` (Next_Followup_Date ≤ today, Follow_Up_Count &lt; 2) and `leads_to_mark_stopped` (Follow_Up_Count ≥ 2).
4. **Prepare actions:** flatten into one list; each item has `company_id`, `b2c_lead_id`, `action` (`mark_stopped` | `create_draft`).
5. If `action === "mark_stopped"`: PATCH mark-outreach-stopped. Else: POST `/api/outbound/create` with `company_id`, `lead_id` (B2C_Lead_ID), **`intent`: "Follow-up Check-in"**, **`trigger_type`: "time_based"**, **`email_type`: "B2C"** (same shape as B2B, so the backend saves `trigger_type` on the email and later Update CRM can increment Follow_Up_Count when the draft is sent).

**When Follow_Up_Count is incremented:** Only when the **draft created by this workflow** is **approved and sent** by **Send Approved Drafts**. That workflow calls Update CRM After Send; the backend sees `email.trigger_type === "time_based"` and `lead_source === "b2c"`, reads current Follow_Up_Count from B2C_FUNNEL, adds 1, and writes it back. The B2C Follow-Up Drafts workflow itself does **not** change Follow_Up_Count; it only creates drafts.

---

## When and which CRM sheets are updated (B2B vs B2C)

B2C logic is **separate** from normal inbound and B2B: different sheets (B2C_FUNNEL vs LEADS) and keyed by **B2C_Lead_ID** (stored as `lead_id` in ACTIVITIES and TASKS for both B2B and B2C).

### On SEND (we send an email to a lead)

| Step | Workflow | Condition | Sheets updated |
|------|----------|-----------|-----------------|
| 1 | **Send Approved Drafts** | After Gmail send + Mark Draft as Sent | — |
| 2 | **Update CRM? (B2B/B2C outbound or reply in thread)** | `email_type === "outbound"` **OR** `recipient_context.lead_id` not empty | See below |
| 3 | **Update CRM After Send** (HTTP POST update-crm) | Only when step 2 is true | **B2B:** LEADS, ACTIVITIES, TASKS (by Lead_ID). **B2C:** B2C_FUNNEL, ACTIVITIES, TASKS (by B2C_Lead_ID as `lead_id`). |

- **B2B:** `lead_id` = Lead_ID from CRM; `lead_source` = "b2b" (default). Backend updates **LEADS**, **ACTIVITIES**, **TASKS**.
- **B2C:** `lead_id` = B2C_Lead_ID; `lead_source` = "b2c". Backend updates **B2C_FUNNEL**, **ACTIVITIES**, **TASKS**. The workflow sends `lead_source` from `recipient_context` so the backend updates B2C_FUNNEL (not LEADS).
- Drafts created via **B2C Follow-Up Drafts** or the B2C Outreach UI have `recipient_context.lead_id` = B2C_Lead_ID and `recipient_context.lead_source` = "b2c" (set when the draft is created by the backend Flow2).

### On REPLY (lead/customer replies to our email)

| Step | Where | What happens | Sheets updated |
|------|--------|----------------|-----------------|
| 1 | Inbound email stored (e.g. n8n → backend POST process email) | Flow1 saves email; if `thread_id` present, attaches `recipient_context` from **thread root** (our outbound) so `lead_id` and `lead_source` are set. | — |
| 2 | Backend | `record_lead_replied_if_applicable(email_id)` is called after storing the inbound email. | **B2B:** LEADS (Stage=Replied, dates), ACTIVITIES (Lead Replied), TASKS (complete follow-up, create Review Reply). **B2C:** B2C_FUNNEL (Stage=Replied, dates), ACTIVITIES, TASKS — same, keyed by **B2C_Lead_ID** when `lead_source === "b2c"`. |

- For B2C reply: the **thread root** is our B2C outbound email, which has `recipient_context.lead_id` = B2C_Lead_ID and `lead_source` = "b2c". So the inbound reply gets that context and CRM updates go to **B2C_FUNNEL**, not LEADS.

### Summary

- **Normal inbound** (no outbound thread): no CRM update from these workflows.
- **B2B outbound / reply:** LEADS + ACTIVITIES + TASKS (Lead_ID).
- **B2C outbound / reply:** B2C_FUNNEL + ACTIVITIES + TASKS (B2C_Lead_ID as `lead_id`). B2C is distinguished in the workflow by `lead_source` and in the backend by updating B2C_FUNNEL when `lead_source === "b2c"`.

---

## Workflow 2: Time-Based Outbound Trigger (Optional)

**Purpose:** Automatically creates outbound drafts for leads with `Next_Followup_Date = today`.

**Trigger:** Schedule (Cron) - Runs hourly

**Steps:**

1. **Schedule Trigger**
   - Type: Cron
   - Cron Expression: `0 * * * *` (every hour)
   - Timezone: Your timezone

2. **HTTP Request: Get All Companies**
   - Method: GET
   - URL: `http://localhost:8000/api/companies/`
   - Headers:
     - `Authorization`: `Bearer {n8n_service_token}`
   - Response: Array of companies

3. **For Each Company:**
   
   a. **HTTP Request: Get B2B Leads**
      - Method: GET
      - URL: `http://localhost:8000/api/outbound/b2b/leads`
      - Query Parameters:
        - `company_id`: `{{ $json.company_id }}`
      - Headers:
        - `Authorization`: `Bearer {n8n_service_token}`
      - Response: Array of leads
   
   b. **Filter: Leads Due Today**
      - Condition: `Next_Followup_Date` equals today's date (YYYY-MM-DD format)
      - Use n8n expression: `{{ $json.Next_Followup_Date === $now.toFormat('yyyy-MM-dd') }}`
   
   c. **For Each Due Lead:**
      
      - **HTTP Request: Create Outbound Draft**
        - Method: POST
        - URL: `http://localhost:8000/api/outbound/create`
        - Headers:
          - `Authorization`: `Bearer {n8n_service_token}`
        - Body:
          ```json
          {
            "company_id": "{{ $json.company_id }}",
            "lead_id": "{{ $json.Lead_ID }}",
            "email_type": "B2B",
            "trigger_type": "time_based"
          }
          ```
        - Response: Draft created confirmation

4. **Error Handling**
   - Log errors but continue processing other leads
   - Send notification if multiple failures occur

**Configuration Notes:**
- This workflow is optional - can be disabled if manual triggers are preferred
- Consider adding a "max drafts per run" limit to avoid overwhelming the system
- Add deduplication logic to prevent creating multiple drafts for the same lead

---

## Workflow 3: Calendar Trigger (Optional)

**Purpose:** Creates follow-up emails after calendar events (meetings, calls).

**Trigger:** Google Calendar Webhook or Schedule

**Steps:**

1. **Google Calendar Trigger**
   - Watch for: Event end
   - Calendar: Company calendar
   - Filter: Events with specific attendees or keywords

2. **Extract Meeting Info**
   - Parse calendar event
   - Extract attendee emails
   - Match to leads in CRM

3. **HTTP Request: Create Outbound Draft**
   - Method: POST
   - URL: `http://localhost:8000/api/outbound/create`
   - Body:
     ```json
     {
       "company_id": "{company_id}",
       "lead_id": "{matched_lead_id}",
       "email_type": "B2B",
       "intent": "schedule_meeting",
       "trigger_type": "calendar"
     }
     ```

---

## Workflow 4: Task Trigger (Optional)

**Purpose:** Creates outbound drafts based on tasks in TASKS.xlsx.

**Trigger:** Schedule (Cron) - Runs every 30 minutes

**Steps:**

1. **Schedule Trigger**
   - Cron Expression: `*/30 * * * *` (every 30 minutes)

2. **HTTP Request: Get Tasks** (if API endpoint exists)
   - OR: Read TASKS.xlsx directly from Google Drive
   - Filter: Tasks with `Due_Date = today` and `Status = Pending`

3. **For Each Task:**
   - Match task to lead
   - Create outbound draft with appropriate intent

---

## n8n Configuration

### Environment Variables

Set these in n8n environment or credentials:

- `BACKEND_API_URL`: `http://localhost:8000`
- `N8N_SERVICE_TOKEN`: JWT token for backend API authentication (if using service account)

### Credentials Setup

1. **Gmail API Credentials**
   - Create OAuth 2.0 credentials in Google Cloud Console
   - Add to n8n as "Google OAuth2 API" credential
   - Scopes: `https://www.googleapis.com/auth/gmail.send`

2. **Backend API Authentication**
   - Option 1: Use JWT service token (recommended for n8n)
   - Option 2: Use Basic Auth
   - Store as n8n credential

### Error Handling

- Add error handling nodes after each HTTP request
- Log errors to n8n execution log
- Send notifications (Slack/Email) for critical failures
- Implement retry logic with exponential backoff

### Rate Limiting

- Gmail API: 250 quota units per user per second
- Add delays between requests if processing multiple drafts
- Use n8n's "Wait" node to space out requests

---

## Testing Workflows

1. **Test Workflow 1:**
   - Manually approve a draft in the UI
   - Wait for next cron run (or trigger manually)
   - Verify email is sent
   - Check CRM sheets are updated

2. **Test Workflow 2:**
   - Set a lead's `Next_Followup_Date` to today
   - Trigger workflow manually
   - Verify draft is created
   - Check draft appears in UI

3. **Test Error Handling:**
   - Disconnect company OAuth
   - Trigger workflow
   - Verify error is caught and logged
   - Verify notification is sent (if configured)

---

## Monitoring

- Monitor n8n execution logs for failures
- Set up alerts for workflow failures
- Track email send success rate
- Monitor CRM update success rate

---

## Notes

- All workflows use company-specific OAuth tokens
- Multi-tenant isolation is maintained at API level
- Workflows can be enabled/disabled per company if needed
- Consider adding workflow execution metrics dashboard

