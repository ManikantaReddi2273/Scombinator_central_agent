# S Combinator — Central Agent Platform

Multi-company AI email operations platform for a **parent company and its spin-offs**.

It turns raw inbox and CRM activity into **classified, prioritized, on-brand drafts** — then a **human always approves before anything is sent**.

---

## Table of contents

1. [Tech stack](#tech-stack)
2. [Prerequisites](#prerequisites)
3. [Complete setup & how to run](#complete-setup--how-to-run)
4. [Environment variables](#environment-variables)
5. [Why this project exists](#why-this-project-exists)
6. [What it does](#what-it-does-product-summary)
7. [Architecture & internal flows](#high-level-architecture)
8. [Docker / n8n vs dashboard-only](#what-needs-docker--n8n-vs-what-does-not)
9. [Deploy to Render](#deploying-to-render-blueprint)
10. [Project structure](#project-structure)
11. [First-time company checklist](#first-time-company-checklist)
12. [Troubleshooting](#troubleshooting)

---

## Tech stack

### Overview

| Layer | Technology | Role |
|-------|------------|------|
| **Frontend** | React 18, TypeScript, Vite 5, Tailwind CSS 3 | Admin dashboard UI |
| | React Router 6, TanStack React Query 5, Zustand | Routing, server state, auth store |
| | Axios, Lucide React, date-fns | HTTP, icons, dates |
| **Backend** | FastAPI 0.104, Uvicorn, Pydantic 2 | REST API |
| | SQLAlchemy 2.0 (async) + asyncpg | PostgreSQL ORM |
| | Alembic, psycopg2-binary | Migrations / sync DB tools |
| **AI** | LangGraph, LangChain, OpenAI (GPT-4o) | Flow 1 & Flow 2 pipelines |
| **Database** | PostgreSQL 15+ | Companies, emails, drafts, logs, admin |
| **Cache** | Redis (optional) | Brand-context cache |
| **Automation** | n8n (Docker image `n8nio/n8n`) | Gmail poll, send, scheduled follow-ups |
| **Integrations** | Gmail, Google Drive, Google Sheets APIs | Inbox, brand docs, CRM |
| **Auth / security** | JWT (`python-jose`), bcrypt, Fernet | Admin login + encrypted OAuth tokens |
| **Deploy** | Render Blueprint (`render.yaml`) | Hosted frontend + backend + Postgres |

### Backend packages (main)

`fastapi`, `uvicorn`, `sqlalchemy`, `asyncpg`, `pydantic`, `langchain`, `langgraph`, `openai`, `google-api-python-client`, `google-auth-oauthlib`, `cryptography`, `httpx`, `python-jose`, `bcrypt`

Full list: `backend/requirements.txt`

### Frontend packages (main)

`react`, `react-dom`, `react-router-dom`, `@tanstack/react-query`, `zustand`, `axios`, `tailwindcss`, `vite`, `typescript`, `lucide-react`

Full list: `frontend/package.json`

---

## Prerequisites

Install these **before** setup:

| Tool | Version | Used for | Check |
|------|---------|----------|-------|
| **Python** | 3.10+ | Backend | `python --version` |
| **Node.js** | 18+ | Frontend | `node --version` |
| **npm** | comes with Node | Frontend deps | `npm --version` |
| **PostgreSQL** | 15+ | Database | `psql --version` |
| **Docker Desktop** | Latest | Local n8n | Docker running in tray |
| **OpenAI API key** | — | AI classify + draft | From platform.openai.com |
| **Google Cloud OAuth client** | — | Gmail + Drive connect | Google Cloud Console |

Optional: Git, a code editor (VS Code / Cursor).

---

## Complete setup & how to run

Follow this order every time you set up a machine:

**PostgreSQL → Backend → Frontend → n8n**

Use a **separate terminal** for each long-running service.

---

### Step 0 — Clone and open the project

```powershell
cd "C:\Users\...\S Combinator _Central Agent Platform"
```

---

### Step 1 — Create the database

Start PostgreSQL, then:

```sql
CREATE DATABASE s_combinator;
```

Remember your Postgres username/password for `backend/.env`.

---

### Step 2 — Backend setup (first time)

> **Important:** the virtual environment folder is **`.venv`** (leading dot), **not** `venv`.

```powershell
cd backend
python -m venv .venv
.\.venv\Scripts\Activate.ps1
pip install -r requirements.txt
```

If PowerShell blocks activation:

```powershell
Set-ExecutionPolicy -ExecutionPolicy RemoteSigned -Scope CurrentUser
```

Create `backend/.env` (copy from the [Environment variables](#environment-variables) section below). Minimum you must set:

- `ADMIN_EMAIL` / `ADMIN_PASSWORD`
- `DATABASE_URL` / `DATABASE_URL_SYNC` / `LANGRAPH_CHECKPOINT_DB_URL`
- `JWT_SECRET_KEY`
- `ENCRYPTION_KEY` (Fernet key)
- `OPENAI_API_KEY`
- `N8N_SERVICE_API_KEY` (any long secret; must match n8n later)

Create tables + admin user:

```powershell
python init_db.py
```

---

### Step 3 — Start the backend (every time)

```powershell
cd backend
.\.venv\Scripts\Activate.ps1
python -m uvicorn main:app --reload --host 0.0.0.0 --port 8000
```

| Check | URL |
|-------|-----|
| Health | http://localhost:8000/health |
| Database | http://localhost:8000/health/db |
| Swagger API docs | http://localhost:8000/docs |

Leave this terminal running.

---

### Step 4 — Frontend setup (first time)

**New terminal:**

```powershell
cd frontend
npm install
```

Create `frontend/.env`:

```env
VITE_API_URL=http://localhost:8000
```

For Google Connect button locally you may also set `VITE_GOOGLE_CLIENT_ID` (same Client ID as Google Cloud).

---

### Step 5 — Start the frontend (every time)

```powershell
cd frontend
npm run dev
```

Open: **http://localhost:3000**  
Log in with `ADMIN_EMAIL` / `ADMIN_PASSWORD` from `backend/.env`.

Leave this terminal running.

---

### Step 6 — n8n setup (first time) — for email automation

1. Start **Docker Desktop** and wait until it is running.
2. **New terminal:**

```powershell
cd n8n
```

3. Create `n8n/.env` with the **same** API key as the backend:

```env
N8N_SERVICE_API_KEY=your-secret-key-here
BACKEND_API_URL=http://host.docker.internal:8000
FRONTEND_URL=http://localhost:3000
```

(`host.docker.internal` lets the n8n container reach your local backend on Windows/Mac.)

4. Start n8n:

```powershell
docker-compose up -d
```

5. Open **http://localhost:5678** and log in with the basic-auth user/password from `n8n/docker-compose.yml`.

6. **Import workflows** (Workflows → Import from File):

| File | What it does |
|------|----------------|
| `Email Ingestion.json` | Polls Gmail → `POST /api/emails/process` |
| `Send Approved Drafts.json` | Sends approved drafts via Gmail |
| `B2B Follow-Up Drafts.json` | Scheduled B2B follow-up drafts |
| `B2C Follow-Up Drafts.json` | Scheduled B2C follow-up drafts |
| `Company OAuth Connection.json` | Optional local OAuth helper |

7. **Activate** the workflows you need.

Useful commands:

```powershell
docker-compose down
docker-compose restart
docker logs -f s-combinator-n8n
```

> Dashboard-only use (view / approve / manage companies) works **without** n8n.  
> Auto inbox polling and auto-send need n8n + Docker.

---

### Step 7 — Daily start (after first-time setup)

Three terminals:

```powershell
# Terminal 1 — Backend
cd backend
.\.venv\Scripts\Activate.ps1
python -m uvicorn main:app --reload --host 0.0.0.0 --port 8000
```

```powershell
# Terminal 2 — Frontend
cd frontend
npm run dev
```

```powershell
# Terminal 3 — n8n (optional but needed for automation)
cd n8n
docker-compose up -d
```

Then open http://localhost:3000.

---

### Local ports

| Service | URL |
|---------|-----|
| Backend API | http://localhost:8000 |
| API docs (Swagger) | http://localhost:8000/docs |
| Frontend | http://localhost:3000 |
| n8n | http://localhost:5678 |
| PostgreSQL | localhost:5432 |

---

## Environment variables

### `backend/.env`

```env
# Admin login (created by init_db.py)
ADMIN_EMAIL=your-admin-email
ADMIN_PASSWORD=your-admin-password
ADMIN_ROLE=ADMIN

# PostgreSQL — change PASSWORD / user to match your install
DATABASE_URL=postgresql+asyncpg://postgres:PASSWORD@localhost:5432/s_combinator
DATABASE_URL_SYNC=postgresql://postgres:PASSWORD@localhost:5432/s_combinator
LANGRAPH_CHECKPOINT_DB_URL=postgresql+asyncpg://postgres:PASSWORD@localhost:5432/s_combinator

# JWT
JWT_SECRET_KEY=long-random-secret
JWT_ALGORITHM=HS256
JWT_ACCESS_TOKEN_EXPIRE_MINUTES=1440

# Fernet key for encrypting Google OAuth tokens in DB
ENCRYPTION_KEY=your-fernet-encryption-key

# OpenAI
OPENAI_API_KEY=your-openai-api-key
OPENAI_MODEL=gpt-4o

# Must match n8n/.env exactly
N8N_WEBHOOK_URL=http://localhost:5678/webhook
N8N_SERVICE_API_KEY=your-secret-key-here

# Google OAuth (needed for Connect Gmail on local/Render)
GOOGLE_CLIENT_ID=
GOOGLE_CLIENT_SECRET=
BACKEND_PUBLIC_URL=http://localhost:8000
FRONTEND_URL=http://localhost:3000

APP_NAME=S Combinator Central Agent Platform
APP_VERSION=1.0.0
DEBUG=True
```

### `frontend/.env`

```env
VITE_API_URL=http://localhost:8000
# VITE_GOOGLE_CLIENT_ID=your-google-oauth-client-id
```

### `n8n/.env`

```env
N8N_SERVICE_API_KEY=your-secret-key-here
BACKEND_API_URL=http://host.docker.internal:8000
FRONTEND_URL=http://localhost:3000
```

> `.env` files are gitignored. **Never commit real secrets.**

---

## Why this project exists

Small teams and multi-brand groups drown in email:

- Important sales or hiring messages get buried
- Replies are inconsistent across brands
- Follow-ups to B2B/B2C leads are manual and easy to miss
- There is no shared priority view across companies

**S Combinator Central Agent Platform** solves that by:

1. Watching each company’s Gmail inbox
2. Understanding each email with AI (function, intent, urgency, impact)
3. Scoring priority into one cross-company queue
4. Drafting a reply in that company’s brand voice
5. Letting an admin review / edit / approve
6. Sending only after approval — then logging outcomes in CRM

**Design principle:**  
`raw input → structured understanding → prioritized decision → editable draft → human approval → logged outcome`

---

## What it does (product summary)

| Capability | Status |
|------------|--------|
| **Flow 1 — Inbound email → draft reply** | Built |
| **Flow 2 — Outbound B2B / B2C follow-up drafts** | Built |
| Multi-company (tenant) isolation | Built |
| Admin dashboard (queue, drafts, emails, companies) | Built |
| Gmail + Google Drive + Sheets CRM | Built |
| Human-in-the-loop (approve before send) | Built |
| **Flow 3 / 4 — Hiring pipelines** | Blueprint only (not coded yet) |

### Dashboard pages

| Page | Purpose |
|------|---------|
| Dashboard | High-level stats |
| Priority Queue | Cross-company emails sorted by AI priority |
| Drafts | Review, edit, approve / reject AI drafts |
| Emails | Browse processed inbound/outbound emails |
| B2B Outbound | Leads from CRM `LEADS` sheet → create drafts |
| B2C Outreach | Leads from CRM `B2C_FUNNEL` → create drafts |
| Companies | Add / connect OAuth / delete companies |

---

## High-level architecture

```
┌─────────────────┐     ┌──────────────────────┐     ┌─────────────────┐
│  React Frontend │────▶│  FastAPI Backend     │────▶│  PostgreSQL     │
│  (admin UI)     │     │  LangGraph + OpenAI  │     │  emails, drafts │
└─────────────────┘     └──────────┬───────────┘     └─────────────────┘
                                   │
                    ┌──────────────┼──────────────┐
                    ▼              ▼              ▼
              ┌─────────┐   ┌──────────┐   ┌────────────┐
              │   n8n   │   │  Gmail   │   │ Drive/Sheets│
              │ poller  │   │  send/   │   │ CRM + brand │
              │ + send  │   │  read    │   │ docs        │
              └─────────┘   └──────────┘   └────────────┘
```

### Who does what

| Layer | Responsibility |
|-------|----------------|
| **Frontend** | Admin login, review queue, approve drafts, manage companies, trigger outbound drafts |
| **Backend** | Auth, tenants, AI pipelines (Flow 1 / Flow 2), CRUD APIs, OAuth token storage, CRM helpers |
| **n8n** | Scheduled jobs: poll Gmail, call backend, send approved mail, scheduled follow-ups |
| **PostgreSQL** | Companies, emails, drafts, candidates, audit logs, admin users |
| **Google** | Gmail inboxes, Drive brand docs, Sheets CRM workbooks |
| **OpenAI** | Classification, scoring, summary, action, draft generation |

### Multi-company (tenant) model

Each **company** is a tenant with:

- Its own Gmail identity (OAuth tokens encrypted in DB)
- Its own Drive folder (CRM + brand context)
- Isolated emails / drafts / candidates / logs

The **admin** sees all companies in one dashboard (unified priority queue).

---

## What happens internally

### A) One-time company setup

1. Admin creates a company (name + email) in the UI  
2. Admin clicks **Connect Gmail & Drive**  
   - On Render: Google OAuth returns to the **backend** callback  
   - Tokens are encrypted and stored on the company row  
3. In that Google account’s Drive, create a **CRM** folder with a workbook containing sheets such as:
   - `LEADS` (B2B)
   - `B2C_FUNNEL` (B2C)
   - `ACTIVITIES`, `TASKS` (as needed)
4. Add brand docs (`COMPANY.md`, `VOICE.md`, `POLICIES.md`, templates, etc.) so drafts stay on-brand  

Templates live in `CRM_TEMPLATES/`.

---

### B) Flow 1 — Inbound email → response (internal path)

**Trigger:** Someone emails a connected company inbox.

```
Gmail inbox
    │
    ▼
n8n Email Ingestion (every ~5 min)
    │  1. Warm up backend (Render cold start)
    │  2. GET /api/companies/with-oauth
    │  3. GET /api/companies/{id}/gmail-token
    │  4. List unread Gmail messages
    │  5. Fetch full message → extract subject/body/from/to/thread
    │  6. POST /api/emails/process  → HTTP 202 Accepted (fast)
    │  7. Mark message as read (best-effort)
    ▼
Backend /process
    │  • Map company_id / credential / to-email → tenant
    │  • Deduplicate by gmail_message_id
    │  • Save email stub ("Queued for AI processing")
    │  • Queue Flow 1 in background (one at a time on free tier)
    ▼
LangGraph Flow 1 (OpenAI)
    │  1. Classify   → function, intent, urgency, impact, confidence
    │  2. Score      → priority 0–100
    │  3. Summarize  → short executive summary
    │  4. Recommend  → next action (reply / ask info / schedule / escalate…)
    │  5. Draft      → on-brand reply using brand context from Drive
    ▼
PostgreSQL
    │  Update email + create pending draft
    ▼
Admin dashboard
    │  Priority Queue / Drafts → review → edit → Approve
    ▼
n8n Send Approved Drafts
    │  Poll approved drafts → send via Gmail → mark sent → update CRM if needed
    ▼
Done (human-approved send)
```

**On Render free tier:** `/process` returns **202** quickly; AI runs in the background. Wait **1–3 minutes** for drafts.

Mermaid diagram: [`PROJECT_FLOW.mmd`](PROJECT_FLOW.mmd) → [mermaid.live](https://mermaid.live).

---

### C) Flow 2 — Outbound (you email leads)

1. **Manual** — B2B / B2C page → **Send email**  
2. **Scheduled** — n8n follow-up workflows  

```
Lead → POST /api/outbound/create → Flow 2 (intent → context → template → draft)
     → Admin approves → n8n sends → CRM updated
```

| Type | CRM source | Typical use |
|------|------------|-------------|
| **B2B** | `LEADS` | Institutions, demos, proposals |
| **B2C** | `B2C_FUNNEL` | Campaigns, social commenters |

Lead replies re-enter **Flow 1**.

---

### D) Human-in-the-loop

```
AI draft (pending) → Admin review/edit → Approve (may send) / Reject (not sent)
```

Nothing is auto-sent without an approval path.

---

### E) Flows 3 & 4 — Hiring

Described in the blueprint; **not implemented in code yet**.

---

## What needs Docker / n8n vs what does not

| You want to… | Need n8n / Docker? |
|--------------|--------------------|
| Open dashboard, login, view emails/drafts | **No** |
| Add company, Connect Gmail (backend callback) | **No** |
| Approve / edit drafts | **No** |
| Create outbound draft from B2B/B2C UI | **No** |
| Auto-poll Gmail | **Yes** |
| Auto-send approved drafts | **Yes** |
| Scheduled B2B/B2C follow-ups | **Yes** |

**Today:** frontend + backend can run on **Render**; n8n usually runs on **this PC via Docker**.  
For fully cloud automation, host n8n separately (always-on preferred). See `n8n/IMPORT_AFTER_RENDER.md`.

### Free Render cold start / 502

- Free services **sleep** when idle  
- First request **wakes** them (30–60s) = **cold start**  
- No timely response from the app → **502 Bad Gateway**  
- Email Ingestion uses warmup + retries to reduce failures  

---

## Deploying to Render (Blueprint)

Root file: `render.yaml`.

Typical URLs:

- Backend: `https://scombinator-backend.onrender.com`
- Frontend: `https://scombinator-frontend.onrender.com`

### Steps

1. Push `main` (including `render.yaml`) to GitHub  
2. Render → **New → Blueprint** → select the repo  
3. Fill secrets: `ADMIN_EMAIL`, `ADMIN_PASSWORD`, `ENCRYPTION_KEY`, `OPENAI_API_KEY`, `N8N_SERVICE_API_KEY`, `GOOGLE_CLIENT_ID`, `GOOGLE_CLIENT_SECRET`, `VITE_GOOGLE_CLIENT_ID`, `FRONTEND_URL`, etc.  
4. Set backend `FRONTEND_URL` to the frontend URL (CORS)  
5. Google Cloud Console redirect URI:  
   `https://scombinator-backend.onrender.com/api/companies/oauth/callback`  
6. Point n8n workflows at the Render backend and re-import JSONs  

DB init runs on boot via `backend/start_render.sh`.  
**n8n is not in the Blueprint by default** — keep Docker local or host n8n separately.

---

## Project structure

```
.
├── backend/                 # FastAPI + LangGraph + PostgreSQL
│   ├── main.py
│   ├── config.py
│   ├── database.py
│   ├── init_db.py           # First-time tables + admin
│   ├── start_render.sh
│   ├── requirements.txt     # Python dependencies
│   ├── auth/
│   ├── models/
│   ├── schemas/
│   ├── routers/
│   └── services/
│       ├── flow1/           # Inbound AI (classify → draft)
│       └── flow2/           # Outbound AI
├── frontend/                # React admin dashboard
│   ├── package.json
│   └── src/
├── n8n/                     # Workflows + docker-compose.yml
├── CRM_TEMPLATES/
├── render.yaml
├── PROJECT_FLOW.mmd
└── README.md                # This file
```

Flow 1 AI nodes: `backend/services/flow1/nodes/`  
(classification → priority → summary → action → draft)

---

## First-time company checklist

1. Backend + frontend running (+ n8n if you want automation)  
2. Log in → **Companies** → **Add Company**  
3. **Connect Gmail & Drive**  
4. Drive: CRM workbook + brand docs  
5. Send a test email to the company inbox  
6. Activate **Email Ingestion** in n8n  
7. Check **Priority Queue** / **Drafts**  
8. Approve a draft → activate **Send Approved Drafts** if you use auto-send  

---

## Troubleshooting

| Symptom | Likely cause | Fix |
|---------|--------------|-----|
| `No module named 'fastapi'` | Wrong venv | `.\.venv\Scripts\Activate.ps1` |
| Script execution disabled | PowerShell policy | `Set-ExecutionPolicy RemoteSigned -Scope CurrentUser` |
| `proxies` / httpx error | Global httpx too new | Use `.venv` (`httpx==0.25.2`) |
| `/health/db` unhealthy | Postgres / bad URL | Start Postgres; fix `DATABASE_URL` |
| Login / CORS errors | Wrong origin | Match `FRONTEND_URL`; use port 3000 locally |
| AI always falls back | Missing `OPENAI_API_KEY` | Set key; restart/redeploy |
| n8n `403` | API key mismatch | Same `N8N_SERVICE_API_KEY` in backend + n8n |
| n8n **502** to Render | Cold start / sleep | Warmup + retries; wait; check Render logs |
| 202 but no draft | AI still running / OpenAI error | Wait 1–3 min; check backend logs |
| OAuth config missing | `VITE_GOOGLE_CLIENT_ID` not set at build | Set on frontend env; redeploy |

---

## Related docs

| Doc | Contents |
|-----|----------|
| [`PROJECT_FLOW.mmd`](PROJECT_FLOW.mmd) | Mermaid end-to-end flow |
| [`Blueprint_ AI Agents Automation (Customer Acquisition and Hiring).md`](Blueprint_%20AI%20Agents%20Automation%20(Customer%20Acquisition%20and%20Hiring).md) | Product blueprint |
| [`n8n/IMPORT_AFTER_RENDER.md`](n8n/IMPORT_AFTER_RENDER.md) | Workflows against Render backend |
| [`backend/API_DOCUMENTATION.md`](backend/API_DOCUMENTATION.md) | API reference |
| [`Outbound_Email_Use_Cases.md`](Outbound_Email_Use_Cases.md) | Outbound scenarios |

---

## License / ownership

Internal S Combinator platform project — multi-tenant customer-acquisition email automation with mandatory human approval before send.
