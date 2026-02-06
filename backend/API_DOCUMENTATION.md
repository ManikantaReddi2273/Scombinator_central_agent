# API Documentation - S Combinator Central Agent Platform

## Base URL
```
http://localhost:8000
```

## Authentication

Most endpoints require JWT authentication. Get a token by logging in:

```http
POST /api/auth/login
Content-Type: application/json

{
  "email": "reddimanikanta2005@gmail.com",
  "password": "R@ddi2273"
}
```

Response:
```json
{
  "access_token": "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...",
  "token_type": "bearer",
  "admin_email": "reddimanikanta2005@gmail.com",
  "role": "ADMIN"
}
```

Use the token in subsequent requests:
```
Authorization: Bearer {access_token}
```

---

## Company Management APIs

### 1. Register Company (Called by n8n)
**POST** `/api/companies/register`

Registers a new company after OAuth completion. Called automatically by n8n workflow.

**Request Body:**
```json
{
  "company_name": "AlphaTech",
  "email": "alphatech@gmail.com",
  "access_token": "ya29.a0AfH6SMC...",
  "refresh_token": "1//0g...",
  "n8n_credential_id": "google_cred_101",
  "expires_in": 3600
}
```

**Response:**
```json
{
  "company_id": "550e8400-e29b-41d4-a716-446655440000",
  "name": "AlphaTech",
  "email": "alphatech@gmail.com",
  "n8n_credential_id": "google_cred_101",
  "status": "active",
  "created_at": "2026-02-04T21:40:01.276Z"
}
```

### 2. List All Companies (Admin Only)
**GET** `/api/companies/`

**Headers:**
```
Authorization: Bearer {token}
```

**Response:**
```json
[
  {
    "company_id": "550e8400-e29b-41d4-a716-446655440000",
    "name": "AlphaTech",
    "email": "alphatech@gmail.com",
    "n8n_credential_id": "google_cred_101",
    "status": "active",
    "created_at": "2026-02-04T21:40:01.276Z"
  }
]
```

### 3. Get Company by ID (Admin Only)
**GET** `/api/companies/{company_id}`

**Headers:**
```
Authorization: Bearer {token}
```

---

## Email Processing APIs

### 1. Process Incoming Email (Called by n8n)
**POST** `/api/emails/process`

Processes an incoming email from n8n. Maps credential to company, loads policies, runs AI classification, and creates draft.

**Request Body:**
```json
{
  "credential_id": "google_cred_101",
  "email_data": {
    "subject": "Price inquiry",
    "body": "Hello, I'm interested in your pricing...",
    "from": "customer@example.com",
    "to": "alphatech@gmail.com",
    "thread_id": "thread_123",
    "gmail_message_id": "msg_456"
  }
}
```

**Response:**
```json
{
  "email_id": "660e8400-e29b-41d4-a716-446655440000",
  "draft_id": "770e8400-e29b-41d4-a716-446655440000",
  "company_id": "550e8400-e29b-41d4-a716-446655440000",
  "status": "processed",
  "priority_score": "75",
  "executive_summary": "Email inquiry received",
  "recommended_action": "Reply with template"
}
```

### 2. List Emails (Admin Only)
**GET** `/api/emails/`

**Query Parameters:**
- `company_id` (optional): Filter by company ID
- `function` (optional): Filter by function (Sales/Hiring/Legal/etc)
- `priority_min` (optional): Minimum priority score (0-100)
- `limit` (optional): Number of results (default: 50, max: 100)

**Headers:**
```
Authorization: Bearer {token}
```

**Example:**
```
GET /api/emails/?company_id=550e8400-e29b-41d4-a716-446655440000&priority_min=70&limit=20
```

**Response:**
```json
[
  {
    "id": "660e8400-e29b-41d4-a716-446655440000",
    "company_id": "550e8400-e29b-41d4-a716-446655440000",
    "subject": "Price inquiry",
    "from_email": "customer@example.com",
    "to_email": "alphatech@gmail.com",
    "function": "Sales",
    "intent": "Inquiry",
    "priority_score": "75",
    "executive_summary": "Customer asking about pricing",
    "recommended_action": "Reply with template",
    "created_at": "2026-02-04T21:45:00.000Z"
  }
]
```

### 3. Get Priority Queue (Admin Only)
**GET** `/api/emails/priority-queue`

Returns unified priority queue across all companies, sorted by priority score.

**Query Parameters:**
- `limit` (optional): Number of results (default: 20, max: 100)

**Headers:**
```
Authorization: Bearer {token}
```

**Response:**
```json
[
  {
    "email_id": "660e8400-e29b-41d4-a716-446655440000",
    "company_id": "550e8400-e29b-41d4-a716-446655440000",
    "company_name": "AlphaTech",
    "company_email": "alphatech@gmail.com",
    "subject": "Price inquiry",
    "from_email": "customer@example.com",
    "priority_score": "90",
    "function": "Sales",
    "intent": "Inquiry",
    "executive_summary": "High-value customer inquiry",
    "recommended_action": "Reply with template",
    "created_at": "2026-02-04T21:45:00.000Z"
  }
]
```

### 4. Get Email by ID (Admin Only)
**GET** `/api/emails/{email_id}`

**Headers:**
```
Authorization: Bearer {token}
```

---

## Draft Management APIs

### 1. List Drafts (Admin Only)
**GET** `/api/drafts/`

**Query Parameters:**
- `company_id` (optional): Filter by company ID
- `status` (optional): Filter by status (pending/approved/rejected/sent)
- `limit` (optional): Number of results (default: 50, max: 100)

**Headers:**
```
Authorization: Bearer {token}
```

**Response:**
```json
[
  {
    "id": "770e8400-e29b-41d4-a716-446655440000",
    "company_id": "550e8400-e29b-41d4-a716-446655440000",
    "email_id": "660e8400-e29b-41d4-a716-446655440000",
    "subject": "Re: Price inquiry",
    "body": "Thank you for your inquiry...",
    "status": "pending",
    "version": "1.0",
    "template_used": "pricing_inquiry_template",
    "created_at": "2026-02-04T21:45:05.000Z"
  }
]
```

### 2. Get Pending Drafts (Admin Only)
**GET** `/api/drafts/pending`

Returns all drafts awaiting approval (main review queue).

**Query Parameters:**
- `company_id` (optional): Filter by company ID
- `limit` (optional): Number of results (default: 20, max: 100)

**Headers:**
```
Authorization: Bearer {token}
```

### 3. Get Draft by ID (Admin Only)
**GET** `/api/drafts/{draft_id}`

**Headers:**
```
Authorization: Bearer {token}
```

### 4. Get Draft Status (Called by n8n)
**GET** `/api/drafts/{draft_id}/status`

Returns draft status for n8n to check if approved.

**Response:**
```json
{
  "id": "770e8400-e29b-41d4-a716-446655440000",
  "status": "approved",
  "approved_by": "2f40c283-5325-4140-9dfa-84275b4b280d",
  "approved_at": "2026-02-04T21:50:00.000Z",
  "sent_at": null
}
```

### 5. Approve Draft (Admin Only)
**POST** `/api/drafts/{draft_id}/approve`

**Request Body:**
```json
{
  "draft_id": "770e8400-e29b-41d4-a716-446655440000",
  "edited_body": "Optional: Edited draft body if admin made changes"
}
```

**Response:**
```json
{
  "draft_id": "770e8400-e29b-41d4-a716-446655440000",
  "status": "approved",
  "message": "Draft approved and ready to send"
}
```

### 6. Reject Draft (Admin Only)
**POST** `/api/drafts/{draft_id}/reject`

**Headers:**
```
Authorization: Bearer {token}
```

**Response:**
```json
{
  "draft_id": "770e8400-e29b-41d4-a716-446655440000",
  "status": "rejected",
  "message": "Draft rejected"
}
```

---

## Health Check

### Health Check
**GET** `/health`

**Response:**
```json
{
  "status": "healthy"
}
```

---

## Error Responses

All endpoints may return these error responses:

**401 Unauthorized:**
```json
{
  "detail": "Could not validate credentials"
}
```

**404 Not Found:**
```json
{
  "detail": "Resource not found"
}
```

**422 Validation Error:**
```json
{
  "detail": [
    {
      "loc": ["body", "email"],
      "msg": "field required",
      "type": "value_error.missing"
    }
  ]
}
```

---

## API Flow Examples

### Complete Email Processing Flow

1. **n8n detects new email** → Calls `POST /api/emails/process`
2. **Backend processes** → Creates email record and draft
3. **Admin reviews** → `GET /api/drafts/pending`
4. **Admin approves** → `POST /api/drafts/{draft_id}/approve`
5. **n8n polls status** → `GET /api/drafts/{draft_id}/status`
6. **n8n sends email** → Uses Gmail API with credential

### Company Onboarding Flow

1. **Admin initiates** → Frontend redirects to n8n OAuth
2. **n8n handles OAuth** → Stores credential
3. **n8n calls backend** → `POST /api/companies/register`
4. **Backend creates company** → Returns company record
5. **Company ready** → n8n can start watching inbox

---

## Interactive API Documentation

Visit `http://localhost:8000/docs` for Swagger UI with interactive testing.

Visit `http://localhost:8000/redoc` for ReDoc documentation.

