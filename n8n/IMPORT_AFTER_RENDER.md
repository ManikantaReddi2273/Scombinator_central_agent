# Import these workflows into n8n (after Render deploy)

Workflows in this folder are pointed at the **Render backend**:

`https://scombinator-backend.onrender.com`

## Before import

1. Ensure `n8n/.env` has:
   - `N8N_SERVICE_API_KEY` = **same** value as Render backend `N8N_SERVICE_API_KEY`
   - `BACKEND_API_URL` / `FRONTEND_URL` (already set for Render)
2. Restart n8n so env loads:
   ```powershell
   cd n8n
   docker-compose down
   docker-compose up -d
   ```
3. Open http://localhost:5678

## Import order (recommended)

| File | Purpose |
|------|---------|
| `Email Ingestion.json` | Poll companies → Gmail → `POST /api/emails/process` |
| `Send Approved Drafts.json` | Poll approved drafts → Gmail send → mark sent → update CRM |
| `B2B Follow-Up Drafts.json` | Cron → B2B leads due → create outbound drafts |
| `B2C Follow-Up Drafts.json` | Cron → B2C leads due → create outbound drafts |
| `Company OAuth Connection.json` | **Optional** — local n8n OAuth webhook. On Render, Connect Gmail uses the **backend** callback instead. |

In n8n: **Workflows → Import from File** → select each JSON → **Activate** the workflow.

## Notes

- Free Render apps sleep when idle; first n8n call may take 30–60s.
- Keep this PC + Docker running for automation to work.
- OAuth for companies on Render: use the dashboard **Connect Gmail & Drive** (backend), not this n8n OAuth workflow.
- If you change the Render backend URL, search-replace `scombinator-backend.onrender.com` in these JSON files and re-import (or edit nodes in n8n).
