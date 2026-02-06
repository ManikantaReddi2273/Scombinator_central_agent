# Backend Setup Guide

## Quick Start

### 1. Install Dependencies

```bash
pip install -r requirements.txt
```

### 2. Setup Environment Variables

**Windows:**
```bash
setup_env.bat
```

**Linux/Mac:**
```bash
chmod +x setup_env.sh
./setup_env.sh
```

Or manually create `.env` file with:

```env
ADMIN_EMAIL=reddimanikanta2005@gmail.com
ADMIN_PASSWORD=R@ddi2273
ADMIN_ROLE=ADMIN

POSTGRES_DB=s_combinator
POSTGRES_USER=postgres
POSTGRES_PASSWORD=reddi2273

DATABASE_URL=postgresql+asyncpg://postgres:reddi2273@localhost:5432/s_combinator
DATABASE_URL_SYNC=postgresql://postgres:reddi2273@localhost:5432/s_combinator
LANGRAPH_CHECKPOINT_DB_URL=postgresql+asyncpg://postgres:reddi2273@localhost:5432/s_combinator

JWT_SECRET_KEY=MfuUwnPbuz5wymlkjQ-EMwypAOgpqxuXt-75kMi4gJU
JWT_ALGORITHM=HS256
JWT_ACCESS_TOKEN_EXPIRE_MINUTES=1440

# Generate encryption key:
python generate_encryption_key.py
# Copy the output to ENCRYPTION_KEY in .env

OPENAI_API_KEY=your-openai-api-key-here
N8N_WEBHOOK_URL=http://localhost:5678/webhook
APP_NAME=S Combinator Central Agent Platform
APP_VERSION=1.0.0
DEBUG=True
```

### 3. Setup PostgreSQL Database

Make sure PostgreSQL is running and create the database:

```sql
CREATE DATABASE s_combinator;
```

### 4. Initialize Database

Run the initialization script:

```bash
python init_db.py
```

This will:
- Create all database tables
- Create admin user with encrypted password
- Admin credentials:
  - Email: `reddimanikanta2005@gmail.com`
  - Password: `R@ddi2273`

### 5. Run the Server

```bash
python main.py
```

Or:

```bash
uvicorn main:app --reload --host 0.0.0.0 --port 8000
```

## API Endpoints

### Authentication
- `POST /api/auth/login` - Admin login

### Companies
- `POST /api/companies/register` - Register company (called by n8n)
- `GET /api/companies/` - List all companies (admin only)
- `GET /api/companies/{company_id}` - Get company by ID (admin only)

### Emails
- `POST /api/emails/process` - Process incoming email (called by n8n)

### Drafts
- `GET /api/drafts/` - List drafts with filters (admin only)
- `GET /api/drafts/{draft_id}` - Get draft by ID (admin only)
- `GET /api/drafts/{draft_id}/status` - Get draft status (called by n8n)
- `POST /api/drafts/{draft_id}/approve` - Approve draft (admin only)

## Testing the API

### 1. Login

```bash
curl -X POST "http://localhost:8000/api/auth/login" \
  -H "Content-Type: application/json" \
  -d '{
    "email": "reddimanikanta2005@gmail.com",
    "password": "R@ddi2273"
  }'
```

Response:
```json
{
  "access_token": "eyJ...",
  "token_type": "bearer",
  "admin_email": "reddimanikanta2005@gmail.com",
  "role": "ADMIN"
}
```

### 2. Use Token for Authenticated Requests

```bash
curl -X GET "http://localhost:8000/api/companies/" \
  -H "Authorization: Bearer YOUR_ACCESS_TOKEN"
```

## API Documentation

Once the server is running, visit:
- Swagger UI: `http://localhost:8000/docs`
- ReDoc: `http://localhost:8000/redoc`

## Architecture

- **FastAPI** - Modern async web framework
- **SQLAlchemy 2.0** - ORM with async support
- **PostgreSQL** - Primary database
- **JWT** - Token-based authentication
- **Fernet Encryption** - Token and password encryption
- **Google APIs** - Drive and Gmail integration
- **LangGraph** - AI agent framework (to be implemented)

## Security Features

1. **Password Encryption**: Admin password is hashed using bcrypt
2. **Token Encryption**: Google OAuth tokens are encrypted at rest
3. **JWT Authentication**: Secure token-based auth
4. **Company Isolation**: All data filtered by `company_id`

## Next Steps

1. Implement LangGraph AI agents
2. Add comprehensive error handling
3. Add Redis caching
4. Add logging and monitoring
5. Add unit and integration tests

