# How to Test: B2B Follow-Up (No Reply by Next_Followup_Date)

This guide explains how to verify that **when a lead does not reply by Next_Followup_Date, the application creates a follow-up draft in the same Gmail thread as the first email**.

---

## Expected behaviour

1. You send a **first outbound email** to a lead (manual or from UI). The email is sent via Gmail and gets a **thread_id** when n8n marks the draft as sent.
2. The lead **does not reply** by **Next_Followup_Date** (e.g. 3 days later).
3. The **B2B Follow-Up Drafts** n8n workflow runs (e.g. daily). It:
   - Calls `GET /api/outbound/b2b/leads-due-for-follow-up?company_id=<id>`
   - Gets leads where `Next_Followup_Date <= today` and `Follow_Up_Count` is 0 or 1.
   - For each such lead, calls `POST /api/outbound/create` with `intent: "Follow-up Check-in"`, `trigger_type: "time_based"`.
4. The backend creates a **new draft** for the same lead and sets the new email’s **thread_id** to the **thread_id of the first sent outbound** for that lead. So when you send the follow-up via Gmail, it appears in the **same thread** as the first email.

---

## Prerequisites

- Backend running (`uv run python main.py` from `backend/`).
- n8n running with workflow **B2B Follow-Up Drafts** imported and enabled.
- At least one **company** with OAuth connected and a **CRM** (Google Sheet) with a **LEADS** sheet.
- **LEADS** has at least one lead with:
  - **Next_Followup_Date** = today or a past date (so the lead is “due” for follow-up).
  - **Follow_Up_Count** = 0 or 1 (not 2, or the lead will be marked “Outreach Stopped” instead of getting a draft).
  - **Stage** not “Replied” and **Status** not “No Response – Outreach Stopped”.
- You have already **sent at least one outbound email** to that lead from this app (so there is an `Email` row with `thread_id` set for that lead). If the first email was never marked as sent with a `thread_id`, the follow-up will still be created but may start a new thread.

---

## Test steps

### 1. Prepare a lead “due for follow-up”

In your **LEADS** sheet (or CRM template):

- Set **Next_Followup_Date** to **today’s date** (YYYY-MM-DD).
- Set **Follow_Up_Count** to **0** (first follow-up) or **1** (second follow-up).
- Ensure **Stage** is not “Replied” and **Status** is not “No Response – Outreach Stopped”.
- Note the **Lead_ID** (e.g. `B2B-001`) and the **company_id** for that company.

### 2. Ensure the first email has a thread_id (optional but recommended)

If you already sent a first outbound to this lead via the app and n8n “Send Approved Drafts” (which calls “Update CRM After Send” and then marks the draft as sent with Gmail’s `thread_id`), the backend will have an `Email` row for that lead with `thread_id` set.  
Then the follow-up draft will use that **same thread_id**.

If you have not sent any email yet:

- Create and send one outbound to this lead through your normal flow (UI + n8n).
- After send, ensure the draft is marked as sent and the email record is updated with the Gmail `thread_id` (your “Mark Draft as Sent” / n8n step should send `thread_id` in the body).

### 3. Run “Get Leads Due for Follow-Up” (manual check)

Call the API (replace with your backend URL and API key):

```bash
curl -s -X GET "http://localhost:8000/api/outbound/b2b/leads-due-for-follow-up?company_id=YOUR_COMPANY_ID" \
  -H "X-API-Key: YOUR_N8N_SERVICE_API_KEY"
```

- You should see your lead in **leads_due_for_draft** (and not in **leads_to_mark_stopped**).
- If the lead is missing, check **Next_Followup_Date**, **Follow_Up_Count**, **Stage**, and **Status** in LEADS.

### 4. Create the follow-up draft (same as n8n)

Call the create endpoint (same as the “Create Follow-Up Draft” node):

```bash
curl -s -X POST "http://localhost:8000/api/outbound/create" \
  -H "Content-Type: application/json" \
  -H "X-API-Key: YOUR_N8N_SERVICE_API_KEY" \
  -d '{
    "company_id": "YOUR_COMPANY_ID",
    "lead_id": "B2B-001",
    "intent": "Follow-up Check-in",
    "trigger_type": "time_based",
    "email_type": "B2B"
  }'
```

- You should get **200** with `email_id`, `draft_id`, `subject`, `recipient`, etc.

### 5. Verify the new email has the same thread_id

- In your database, open the **emails** table and find the row with the returned `email_id`.
- Check **thread_id**:
  - It should be **equal to** the **thread_id** of the **first outbound** email for that lead (same `company_id`, same lead in `recipient_context`).
- If the first outbound had no `thread_id` (e.g. never marked as sent with Gmail thread_id), the follow-up may have `thread_id` = NULL; behaviour is then “new thread” when sent.

### 6. Run the full n8n workflow (end-to-end)

- In n8n, open **B2B Follow-Up Drafts** and run it **manually** (Execute Workflow).
- For the lead you prepared, you should see:
  - **Get Leads Due for Follow-Up** → returns the lead in `leads_due_for_draft`.
  - **Prepare Actions** → outputs an action with `action: "create_draft"`.
  - **Mark Stopped or Create Draft?** → False branch.
  - **Create Follow-Up Draft** → HTTP 200, new draft created.
- In the app (Drafts / Emails), you should see the new draft for that lead. In the DB, that email’s **thread_id** should match the first outbound’s **thread_id** for that lead (when the first email had thread_id set).

---

## Quick checklist

| Step | What to check |
|------|----------------|
| LEADS | Lead has Next_Followup_Date ≤ today, Follow_Up_Count 0 or 1, Stage ≠ Replied, Status ≠ No Response – Outreach Stopped |
| API leads-due | GET leads-due-for-follow-up returns this lead in `leads_due_for_draft` |
| API create | POST /api/outbound/create with trigger_type=time_based returns 200 and draft_id |
| DB | New email row has thread_id = first outbound’s thread_id for that lead (if first had thread_id) |
| n8n | B2B Follow-Up Drafts run creates one draft for the lead and no errors |

---

## Troubleshooting

- **Lead not in leads_due_for_draft**  
  Check Next_Followup_Date (must be ≤ today), Follow_Up_Count (0 or 1), Stage/Status, and that the company has OAuth connected.

- **Follow-up draft has thread_id = NULL**  
  The first outbound for this lead either was never sent or was never updated with Gmail’s thread_id when marked as sent. Ensure “Mark Draft as Sent” (or equivalent) sends `thread_id` in the request body and the backend persists it on the Email row.

- **403 on API**  
  Use the same `N8N_SERVICE_API_KEY` in the request header (or query param) as in backend `.env`.

- **404 Lead not found**  
  Confirm `lead_id` and `company_id` match the CRM and that the LEADS sheet is readable (e.g. correct sheet name and permissions).
