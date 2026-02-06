# S Combinator Central Agent Platform - Backend

Backend API for the S Combinator Central Agent Platform.

## Setup

### 1. Install Dependencies

```bash
pip install -r requirements.txt
```

### 2. Configure Environment

Copy `.env.example` to `.env` and update with your values:

```bash
cp .env.example .env
```

Update the following in `.env`:
- Database credentials
- JWT secret key
- Encryption key (32 bytes)
- OpenAI API key (for LangGraph)

### 3. Setup Database

Make sure PostgreSQL is running with the database `s_combinator` created.

### 4. Initialize Database

Run the initialization script to create tables and admin user:

```bash
python init_db.py
```

This will:
- Create all database tables
- Create admin user with encrypted password
- Admin email: `reddimanikanta2005@gmail.com`
- Admin password: `R@ddi2273`

### 5. Run the Server

```bash
python main.py
```

Or using uvicorn directly:

```bash
uvicorn main:app --reload --host 0.0.0.0 --port 8000
```

API will be available at: `http://localhost:8000`

API Documentation: `http://localhost:8000/docs`

## API Endpoints

### Authentication
- `POST /api/auth/login` - Admin login

### Companies
- `POST /api/companies/register` - Register company (called by n8n)
- `GET /api/companies/` - List all companies
- `GET /api/companies/{company_id}` - Get company by ID

### Emails
- `POST /api/emails/process` - Process incoming email (called by n8n)

### Drafts
- `GET /api/drafts/` - List drafts (with filters)
- `GET /api/drafts/{draft_id}` - Get draft by ID
- `GET /api/drafts/{draft_id}/status` - Get draft status (called by n8n)
- `POST /api/drafts/{draft_id}/approve` - Approve draft

## Architecture

- **FastAPI** - Web framework
- **SQLAlchemy 2.0** - ORM with async support
- **PostgreSQL** - Database
- **JWT** - Authentication
- **LangGraph** - AI agent framework (to be implemented)
- **Google APIs** - Drive and Gmail access

## Project Structure

```
backend/
├── main.py              # FastAPI app
├── config.py            # Configuration
├── database.py          # Database setup
├── init_db.py           # Database initialization
├── models/              # Database models
├── schemas/             # Pydantic schemas
├── routers/             # API routes
├── services/            # Business logic
│   ├── encryption.py    # Encryption service
│   ├── token_manager.py # Token management
│   ├── google_api.py    # Google API client
│   ├── tenant.py        # Tenant service
│   ├── policy_loader.py # Policy loader
│   └── audit_logger.py  # Audit logging
└── auth/                # Authentication
```

## Next Steps

1. Implement LangGraph AI agents for email classification and draft generation
2. Add more comprehensive error handling
3. Add Redis for caching
4. Add comprehensive logging
5. Add unit tests
6. Add API rate limiting

