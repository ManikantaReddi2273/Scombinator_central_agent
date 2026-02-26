# n8n Workflow: Time-Based Outbound Trigger

## Overview

This workflow automatically creates outbound email drafts for B2B leads when their `Next_Followup_Date` matches today's date.

## Workflow Configuration

### Trigger
- **Type:** Schedule (Cron)
- **Cron Expression:** `0 * * * *` (runs at the start of every hour)
- **Timezone:** Configure based on your business hours

### Workflow Steps

1. **Get All Companies**
   - HTTP Request: `GET /api/companies/`
   - Returns: List of all active companies

2. **For Each Company:**
   
   a. **Get B2B Leads**
      - HTTP Request: `GET /api/outbound/b2b/leads?company_id={company_id}`
      - Returns: List of B2B leads for the company
   
   b. **Filter Leads Due Today**
      - Filter Node
      - Condition: `Next_Followup_Date === today (YYYY-MM-DD)`
      - Expression: `{{ $json.Next_Followup_Date === $now.toFormat('yyyy-MM-dd') }}`
   
   c. **For Each Due Lead:**
      
      - **Create Outbound Draft**
        - HTTP Request: `POST /api/outbound/create`
        - Body:
          ```json
          {
            "company_id": "{{ $json.company_id }}",
            "lead_id": "{{ $json.Lead_ID }}",
            "email_type": "B2B",
            "trigger_type": "time_based"
          }
        ```
        - Response: Draft created with `draft_id`

3. **Error Handling**
   - Catch errors for individual lead processing
   - Continue processing other leads even if one fails
   - Log errors for review

## Configuration

- **Backend API URL:** `http://localhost:8000` (or your backend URL)
- **Authentication:** Use JWT service token or Basic Auth
- **Max Leads Per Run:** Consider limiting to avoid overwhelming system (e.g., 50 leads max per company per run)

## Notes

- This workflow is optional - can be disabled if manual triggers are preferred
- Leads are filtered by company to maintain multi-tenant isolation
- Drafts created by this workflow will appear in the UI for review and approval
- The workflow does NOT send emails automatically - it only creates drafts

