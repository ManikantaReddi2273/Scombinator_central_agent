# n8n Workflows for Flow 2 (B2B Outbound Email)

This document describes the n8n workflows needed for Flow 2 (B2B Outbound Email) functionality.

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
      - Body (minimum; all other fields are optional or derived from company playbook):
        ```json
        {
          "lead_id": "{{ $('Get Email Info').item.json.recipient_context.lead_id }}",
          "activity_summary": "Sent email: {{ $json.subject }}"
        }
        ```
      - Optional body fields (override backend defaults): `stage`, `engagement_level`, `owner`, `status`, `objection_notes`, `notes`, `next_followup_date`.
      - Backend behavior:
        - **LEADS**: Updates Stage (e.g. "Email Sent"), Engagement_Level (High/Medium/Low), Owner (company name), Last_Activity_Date (send date), Next_Followup_Date (from company PLAYBOOKS.md, e.g. 3 days), Status, Objection_Notes, Notes — all linked by `lead_id`.
        - **ACTIVITIES**: Appends one row (email_sent) linked by `lead_id`.
        - **TASKS**: Creates follow-up task linked by `lead_id`.
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

