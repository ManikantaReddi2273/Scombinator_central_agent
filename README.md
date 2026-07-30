# S Combinator — Central Agent Platform

Multi-company AI agent platform that automates **customer acquisition** email operations for a parent company and its spin-offs.

AI reads inbound email, classifies it, scores priority, and drafts an on-brand reply. It also drafts B2B/B2C outbound follow-ups from CRM data. **A human always approves before anything is sent.**

- **Flow 1 — Inbound:** email → classify → score → summarize → recommend action → draft
- **Flow 2 — Outbound:** intent → recipient context → template → draft
- **Flows 3 & 4 — Hiring:** designed in the blueprint, not implemented yet

See [`PROJECT_FLOW_DIAGRAMS.md`](PROJECT_FLOW_DIAGRAMS.md) for diagrams of every flow.

---

## Tech Stack

| Layer | Technology |
|-------|-----------|
| Frontend | React 18, TypeScript, Vite, Tailwind CSS, React Query, Zustand |
| Backend | FastAPI, Python 3.10+, SQLAlchemy 2.0 (async), asyncpg |
| AI | LangGraph, OpenAI |
| Database | PostgreSQL 15+, Redis (optional cache) |
| Automation | n8n (Docker) |
| Integrations | Gmail, Google Drive, Google Sheets (CRM) |
| Auth | JWT (admin), shared API key (n8n), Fernet encryption for OAuth tokens |

---

## Prerequisites

| Tool | Version | Required for |
|------|---------|--------------|
| Python | 3.10+ | Backend |
| Node.js | 18+ | Frontend |
| PostgreSQL | 15+ | Database |
| Docker Desktop | Latest | n8n automation |
| OpenAI API key | — | AI classification and drafting |

---

## How to Run

Start services in this order: **PostgreSQL → Backend → Frontend → n8n**.

Each service needs its **own terminal** and keeps running.

### 0. PostgreSQL

Make sure PostgreSQL is running, and the database exists:

```sql
CREATE DATABASE s_combinator;
```

---

### 1. Backend — http://localhost:8000

> **Important:** this project's virtual environment is **`.venv`** (with a leading dot), not `venv`.
> Activating the wrong folder name is the most common cause of `ModuleNotFoundError: No module named 'fastapi'`.

```powershell
cd backend
```

**First time only** — create the environment and install dependencies:

```powershell
python -m venv .venv
.\.venv\Scripts\Activate.ps1
pip install -r requirements.txt
```

If PowerShell blocks activation with a script-execution error, run this once:

```powershell
Set-ExecutionPolicy -ExecutionPolicy RemoteSigned -Scope CurrentUser
```

**First time only** — create `backend/.env` (see [Environment Variables](#environment-variables)), then initialize the database:

```powershell
python init_db.py
```

**Every time** — activate and start the server:

```powershell
.\.venv\Scripts\Activate.ps1
python -m uvicorn main:app --reload --host 0.0.0.0 --port 8000
```

Verify:

| Check | URL |
|-------|-----|
| Health | http://localhost:8000/health |
| Database connected | http://localhost:8000/health/db |
| API docs (Swagger) | http://localhost:8000/docs |

---

### 2. Frontend — http://localhost:3000

In a **new terminal**:

```powershell
cd frontend
```

**First time only:**

```powershell
npm install
```

Create `frontend/.env`:

```env
VITE_API_URL=http://localhost:8000
```

**Every time:**

```powershell
npm run dev
```

Open http://localhost:3000 and log in with the admin credentials from `backend/.env`.

> The backend must already be running on port 8000 — Vite proxies `/api` requests to it.

---

### 3. n8n — http://localhost:5678

In a **new terminal**, with Docker Desktop running:

```powershell
cd n8n
```

**First time only** — create `n8n/.env` with the **same** key you set in `backend/.env`:

```env
N8N_SERVICE_API_KEY=your-secret-key-here
```

**Every time:**

```powershell
docker-compose up -d
```

Open http://localhost:5678 and log in using the credentials in `n8n/docker-compose.yml`.

**First time only** — import the workflow files from the `n8n/` folder:

| Workflow | Purpose |
|----------|---------|
| `Email Ingestion.json` | Gmail → backend (Flow 1) |
| `Company OAuth Connection.json` | Connect a company's Gmail + Drive |
| `Send Approved Drafts.json` | Poll approved drafts → send via Gmail |
| `B2B Follow-Up Drafts.json` | Scheduled B2B follow-ups |
| `B2C Follow-Up Drafts.json` | Scheduled B2C follow-ups |

Useful commands:

```powershell
docker-compose down          # stop
docker-compose restart       # restart
docker logs -f s-combinator-n8n   # view logs
```

---

## Deploying to Render (Blueprint)

Render’s **New Blueprint** flow looks for a root file named `render.yaml` on your selected branch (usually `main`). This repo includes that file.

1. Commit and push `render.yaml` (and related deploy files) to GitHub `main`.
2. In Render → **New → Blueprint** → select `ManikantaReddi2273/Scombinator_central_agent` → branch `main`.
3. Fill secrets when prompted: `ADMIN_EMAIL`, `ADMIN_PASSWORD`, `ENCRYPTION_KEY`, `OPENAI_API_KEY`, `N8N_SERVICE_API_KEY`, `N8N_WEBHOOK_URL`, `FRONTEND_URL`.
4. After the frontend URL exists, set backend `FRONTEND_URL` to that URL (e.g. `https://scombinator-frontend.onrender.com`) and redeploy the backend so CORS works.
5. SSH/shell into the backend once and run `python init_db.py` (or use Render Shell) to create tables + admin user.

**Alternative (no Blueprint):** create a **Web Service** for `backend/` and a **Static Site** for `frontend/` manually in the Render dashboard — then `render.yaml` is not required.

**Not on Render by default:** n8n stays on Docker (local or another host). Point it at your Render backend URL.

---


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
# Terminal 3 — n8n
cd n8n
docker-compose up -d
```

---

## Ports

| Service | URL |
|---------|-----|
| Backend API | http://localhost:8000 |
| API docs | http://localhost:8000/docs |
| Frontend | http://localhost:3000 |
| n8n | http://localhost:5678 |
| PostgreSQL | localhost:5432 |

---

## Environment Variables

### `backend/.env`

```env
# Admin login (created by init_db.py)
ADMIN_EMAIL=your-admin-email
ADMIN_PASSWORD=your-admin-password
ADMIN_ROLE=ADMIN

# PostgreSQL
DATABASE_URL=postgresql+asyncpg://postgres:PASSWORD@localhost:5432/s_combinator
DATABASE_URL_SYNC=postgresql://postgres:PASSWORD@localhost:5432/s_combinator
LANGRAPH_CHECKPOINT_DB_URL=postgresql+asyncpg://postgres:PASSWORD@localhost:5432/s_combinator

# JWT
JWT_SECRET_KEY=long-random-secret
JWT_ALGORITHM=HS256
JWT_ACCESS_TOKEN_EXPIRE_MINUTES=1440

# Encryption for stored OAuth tokens — generate with: python generate_encryption_key.py
ENCRYPTION_KEY=your-generated-fernet-key

# OpenAI
OPENAI_API_KEY=your-openai-api-key
OPENAI_MODEL=gpt-4o

# n8n — must match n8n/.env exactly
N8N_WEBHOOK_URL=http://localhost:5678/webhook
N8N_SERVICE_API_KEY=your-secret-key-here

APP_NAME=S Combinator Central Agent Platform
APP_VERSION=1.0.0
DEBUG=True
```

### `frontend/.env`

```env
VITE_API_URL=http://localhost:8000
```

### `n8n/.env`

```env
N8N_SERVICE_API_KEY=your-secret-key-here
```

> `.env` files are gitignored. Never commit real secrets.

---

## Troubleshooting

| Error | Cause | Fix |
|-------|-------|-----|
| `No module named 'fastapi'` / `No module named uvicorn` | Wrong or empty virtual environment activated | Use `.\.venv\Scripts\Activate.ps1` — note the **leading dot**. Confirm with `python -c "import fastapi"` |
| `.\venv\Scripts\activate` not recognized | The folder is `.venv`, not `venv` | Run `.\.venv\Scripts\Activate.ps1` |
| `running scripts is disabled on this system` | PowerShell execution policy | `Set-ExecutionPolicy -ExecutionPolicy RemoteSigned -Scope CurrentUser` |
| `AsyncClient.__init__() got an unexpected keyword argument 'proxies'` | `httpx` 0.28+ with older `openai` | Install the pinned version: `pip install "httpx==0.25.2"` — or just use `.venv`, which has correct pins |
| `database disconnected` at `/health/db` | PostgreSQL not running, or wrong `DATABASE_URL` | Start PostgreSQL; verify the `s_combinator` database exists |
| Frontend login fails / CORS error | Backend not on port 8000, or wrong frontend port | Backend allows `localhost:3000` only — run the frontend on 3000 |
| AI steps return fallback defaults | Missing or invalid `OPENAI_API_KEY` | Set a valid key in `backend/.env` and restart |
| n8n gets `403 Not authenticated` | `N8N_SERVICE_API_KEY` mismatch | Use the identical value in `backend/.env` and `n8n/.env`, then `docker-compose down && docker-compose up -d` |
| `PostgreSQL checkpointing not available` on startup | `langgraph 0.0.20` has no Postgres checkpointer | Harmless — the graph falls back to running without checkpointing |

> **Do not create a second environment named `venv`.** Two environments in `backend/` is what causes the intermittent `ModuleNotFoundError`. This project uses `.venv` only.

---

## Project Structure

```
.
├── backend/              # FastAPI + LangGraph + PostgreSQL
│   ├── main.py           # App entry point
│   ├── config.py         # Env settings
│   ├── database.py       # Async DB engine + session
│   ├── init_db.py        # First-time table + admin setup
│   ├── auth/             # JWT + n8n API key auth
│   ├── models/           # SQLAlchemy tables
│   ├── schemas/          # Pydantic request/response
│   ├── routers/          # API endpoints
│   └── services/         # Business logic
│       ├── flow1/        # Inbound AI pipeline
│       └── flow2/        # Outbound AI pipeline
├── frontend/             # React admin dashboard
├── n8n/                  # Workflow automation (Docker)
├── CRM_TEMPLATES/        # Google Sheets CRM templates
├── docs/                 # Diagrams and test scenarios
└── PROJECT_FLOW_DIAGRAMS.md
```

---

## First-Time Company Setup

Once all three services run:

1. Log in to the dashboard at http://localhost:3000
2. Go to **Companies** → add a company (name + email)
3. Click **Connect Gmail & Drive** to run the OAuth flow through n8n
4. In that company's Google Drive, create a `CRM` folder containing a workbook with `LEADS`, `B2C_FUNNEL`, `ACTIVITIES`, and `TASKS` worksheets (templates in `CRM_TEMPLATES/`)
5. Add brand context documents (`COMPANY.md`, `VOICE.md`, `POLICIES.md`) so drafts stay on-brand
