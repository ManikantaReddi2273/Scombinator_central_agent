# Database Structure Documentation

## Overview

This document provides a comprehensive overview of the database schema for the **S Combinator Central Agent Platform**. The database is built on **PostgreSQL** and uses **SQLAlchemy ORM** with async support.

### Database Technology
- **Database**: PostgreSQL
- **ORM**: SQLAlchemy (Async)
- **Connection Pooling**: Enabled with connection recycling
- **UUID Primary Keys**: All tables use UUID v4 as primary keys

---

## Table of Contents

1. [Database Architecture](#database-architecture)
2. [Tables Overview](#tables-overview)
3. [Detailed Table Schemas](#detailed-table-schemas)
4. [Relationships Diagram](#relationships-diagram)
5. [Indexes and Constraints](#indexes-and-constraints)
6. [Data Flow](#data-flow)

---

## Database Architecture

### Core Principles

1. **Multi-Tenancy**: All business data is isolated by `company_id`
2. **Audit Trail**: Complete logging of all actions via `audit_logs` table
3. **Soft Relationships**: Foreign keys ensure referential integrity
4. **Encryption**: Sensitive tokens are encrypted before storage
5. **Timestamps**: All tables track `created_at` and `updated_at`

### Design Patterns

- **UUID Primary Keys**: All tables use UUID for distributed system compatibility
- **Cascade Deletes**: Child records are automatically deleted when parent is deleted
- **Nullable OAuth Fields**: Support for two-step company registration
- **JSON Metadata**: Flexible storage for AI responses and extra data

---

## Tables Overview

| Table Name | Purpose | Key Relationships |
|------------|---------|-------------------|
| `admins` | Platform administrators | None (standalone) |
| `companies` | Multi-tenant company/tenant data | Parent to: emails, drafts, candidates, audit_logs |
| `emails` | Inbound/outbound email records | Belongs to: company, Parent to: drafts |
| `drafts` | AI-generated email drafts | Belongs to: company, email |
| `candidates` | Hiring pipeline data | Belongs to: company |
| `audit_logs` | System action audit trail | Belongs to: company (optional) |

**Total Tables**: 6

---

## Detailed Table Schemas

### 1. `admins` Table

**Purpose**: Stores platform administrator accounts

| Column Name | Data Type | Constraints | Description |
|-------------|-----------|-------------|-------------|
| `id` | UUID | PRIMARY KEY, NOT NULL, DEFAULT uuid_generate_v4() | Unique admin identifier |
| `email` | VARCHAR(255) | UNIQUE, NOT NULL, INDEXED | Admin email (login) |
| `encrypted_password` | VARCHAR(255) | NOT NULL | Encrypted password hash |
| `role` | VARCHAR(50) | NOT NULL, DEFAULT 'ADMIN' | Admin role (currently only 'ADMIN') |
| `is_active` | BOOLEAN | NOT NULL, DEFAULT true | Account active status |
| `created_at` | TIMESTAMP WITH TIME ZONE | NOT NULL, DEFAULT now() | Record creation timestamp |
| `updated_at` | TIMESTAMP WITH TIME ZONE | NOT NULL, DEFAULT now() | Record update timestamp |

**Relationships**: None (standalone table)

**Indexes**:
- Primary key on `id`
- Unique index on `email`
- Index on `email` for fast lookups

**Notes**:
- Single admin model (no multi-admin support yet)
- Passwords are encrypted before storage
- `is_active` allows soft deletion

---

### 2. `companies` Table

**Purpose**: Multi-tenant company/tenant data storage

| Column Name | Data Type | Constraints | Description |
|-------------|-----------|-------------|-------------|
| `company_id` | UUID | PRIMARY KEY, NOT NULL, DEFAULT uuid_generate_v4() | Unique company identifier |
| `name` | VARCHAR(255) | UNIQUE, NOT NULL, INDEXED | Company name (must be unique) |
| `email` | VARCHAR(255) | UNIQUE, NOT NULL, INDEXED | Company email (Gmail for OAuth) |
| `encrypted_access_token` | TEXT | NULLABLE | Encrypted Google OAuth access token |
| `encrypted_refresh_token` | TEXT | NULLABLE | Encrypted Google OAuth refresh token |
| `access_token_expires_at` | TIMESTAMP WITH TIME ZONE | NULLABLE | Token expiration timestamp |
| `n8n_credential_id` | VARCHAR(255) | NULLABLE, INDEXED | n8n credential ID for this company |
| `status` | VARCHAR(50) | NOT NULL, DEFAULT 'active', INDEXED | Company status (active/inactive) |
| `created_at` | TIMESTAMP WITH TIME ZONE | NOT NULL, DEFAULT now() | Record creation timestamp |
| `updated_at` | TIMESTAMP WITH TIME ZONE | NOT NULL, DEFAULT now() | Record update timestamp |

**Relationships**:
- **One-to-Many** with `emails` (cascade delete)
- **One-to-Many** with `drafts` (cascade delete)
- **One-to-Many** with `candidates` (cascade delete)
- **One-to-Many** with `audit_logs` (cascade delete)

**Indexes**:
- Primary key on `company_id`
- Unique index on `name`
- Unique index on `email`
- Index on `name` for fast lookups
- Index on `email` for fast lookups
- Index on `status` for filtering
- Index on `n8n_credential_id` for n8n integration

**Notes**:
- **Two-Step Registration**: OAuth tokens are nullable to support companies without OAuth initially
- **Unique Name Constraint**: Company names must be unique across the platform
- **Unique Email Constraint**: Company emails must be unique (one company per email)
- **Token Encryption**: Access and refresh tokens are encrypted before storage
- **n8n Integration**: `n8n_credential_id` links to n8n workflow credentials

**Business Rules**:
- Company can exist without OAuth tokens (two-step registration)
- Once OAuth is connected, tokens are required for Gmail/Drive access
- Deleting a company cascades to all related records

---

### 3. `emails` Table

**Purpose**: Stores inbound and outbound email records with AI classification

| Column Name | Data Type | Constraints | Description |
|-------------|-----------|-------------|-------------|
| `id` | UUID | PRIMARY KEY, NOT NULL, DEFAULT uuid_generate_v4() | Unique email identifier |
| `company_id` | UUID | FOREIGN KEY → companies.company_id, NOT NULL, INDEXED | Parent company |
| `subject` | VARCHAR(500) | NOT NULL | Email subject line |
| `body` | TEXT | NOT NULL | Email body content |
| `from_email` | VARCHAR(255) | NOT NULL, INDEXED | Sender email address |
| `to_email` | VARCHAR(255) | NOT NULL, INDEXED | Recipient email address |
| `thread_id` | VARCHAR(255) | NULLABLE, INDEXED | Gmail thread ID for conversation grouping |
| `gmail_message_id` | VARCHAR(255) | NULLABLE, UNIQUE, INDEXED | Gmail message ID (prevents duplicates) |
| `function` | VARCHAR(50) | NULLABLE | AI classification: Sales/Hiring/Legal/Support/Ops/Marketing/Admin |
| `intent` | VARCHAR(50) | NULLABLE | AI classification: Inquiry/Follow-up/Objection/Scheduling/Application/FAQ/Complaint |
| `urgency` | VARCHAR(50) | NULLABLE | AI classification: Immediate/Soon/Can wait |
| `impact` | VARCHAR(50) | NULLABLE | AI classification: Revenue/Hiring/Brand/Low |
| `confidence` | VARCHAR(50) | NULLABLE | AI classification: Clear/Ambiguous/Missing info |
| `priority_score` | VARCHAR(10) | NULLABLE, INDEXED | Numeric priority score (0-100) |
| `executive_summary` | TEXT | NULLABLE | AI-generated 1-2 line summary |
| `recommended_action` | VARCHAR(100) | NULLABLE | AI recommendation: Reply/Schedule/Hold/Escalate |
| `classification_metadata` | JSON | NULLABLE | Full AI classification response (structured data) |
| `created_at` | TIMESTAMP WITH TIME ZONE | NOT NULL, DEFAULT now(), INDEXED | Record creation timestamp |
| `updated_at` | TIMESTAMP WITH TIME ZONE | NOT NULL, DEFAULT now() | Record update timestamp |

**Relationships**:
- **Many-to-One** with `companies` (required)
- **One-to-Many** with `drafts` (cascade delete)

**Indexes**:
- Primary key on `id`
- Foreign key index on `company_id`
- Index on `from_email` for sender lookups
- Index on `to_email` for recipient lookups
- Index on `thread_id` for conversation grouping
- Unique index on `gmail_message_id` (prevents duplicate imports)
- Index on `priority_score` for queue sorting
- Index on `created_at` for time-based queries

**Notes**:
- **AI Classification**: Multiple classification fields populated by AI agents
- **Thread Support**: `thread_id` groups related emails into conversations
- **Duplicate Prevention**: `gmail_message_id` ensures emails aren't imported twice
- **Priority Queue**: `priority_score` enables unified cross-company priority queue
- **Metadata Storage**: `classification_metadata` stores full AI response for debugging

**Business Rules**:
- Every email must belong to a company (multi-tenancy)
- Gmail message IDs must be unique (prevents duplicate processing)
- Priority score is calculated by AI agents based on classification

---

### 4. `drafts` Table

**Purpose**: Stores AI-generated email drafts awaiting human approval

| Column Name | Data Type | Constraints | Description |
|-------------|-----------|-------------|-------------|
| `id` | UUID | PRIMARY KEY, NOT NULL, DEFAULT uuid_generate_v4() | Unique draft identifier |
| `company_id` | UUID | FOREIGN KEY → companies.company_id, NOT NULL, INDEXED | Parent company |
| `email_id` | UUID | FOREIGN KEY → emails.id, NULLABLE, INDEXED | Related email (if responding to inbound) |
| `subject` | VARCHAR(500) | NOT NULL | Draft email subject |
| `body` | TEXT | NOT NULL | Draft email body |
| `status` | VARCHAR(50) | NOT NULL, DEFAULT 'pending', INDEXED | Draft status: pending/approved/rejected/sent |
| `approved_by` | UUID | NULLABLE | Admin ID who approved the draft |
| `approved_at` | TIMESTAMP WITH TIME ZONE | NULLABLE | Approval timestamp |
| `version` | VARCHAR(10) | NOT NULL, DEFAULT '1.0' | Draft version number |
| `is_edited` | BOOLEAN | NOT NULL, DEFAULT false | Whether human edited the draft |
| `original_body` | TEXT | NULLABLE | Original AI-generated body (before edits) |
| `template_used` | VARCHAR(255) | NULLABLE | Template name used for generation |
| `variables_used` | TEXT | NULLABLE | JSON string of template variables |
| `created_at` | TIMESTAMP WITH TIME ZONE | NOT NULL, DEFAULT now(), INDEXED | Record creation timestamp |
| `updated_at` | TIMESTAMP WITH TIME ZONE | NOT NULL, DEFAULT now() | Record update timestamp |
| `sent_at` | TIMESTAMP WITH TIME ZONE | NULLABLE | When draft was sent (if status = 'sent') |

**Relationships**:
- **Many-to-One** with `companies` (required)
- **Many-to-One** with `emails` (optional - only for inbound responses)

**Indexes**:
- Primary key on `id`
- Foreign key index on `company_id`
- Foreign key index on `email_id`
- Index on `status` for filtering (pending/approved/rejected/sent)
- Index on `created_at` for time-based queries

**Notes**:
- **Human-in-the-Loop**: All drafts require human approval before sending
- **Version Tracking**: Supports multiple versions of a draft
- **Edit Tracking**: `is_edited` and `original_body` track human modifications
- **Template Support**: Tracks which template and variables were used
- **Optional Email Link**: `email_id` is nullable for outbound drafts

**Business Rules**:
- Drafts can be created for inbound responses or outbound emails
- Only approved drafts can be sent
- Human edits are tracked for quality improvement
- Deleting a company cascades to all its drafts

---

### 5. `candidates` Table

**Purpose**: Stores hiring pipeline data with AI evaluation

| Column Name | Data Type | Constraints | Description |
|-------------|-----------|-------------|-------------|
| `id` | UUID | PRIMARY KEY, NOT NULL, DEFAULT uuid_generate_v4() | Unique candidate identifier |
| `company_id` | UUID | FOREIGN KEY → companies.company_id, NOT NULL, INDEXED | Parent company |
| `name` | VARCHAR(255) | NOT NULL | Candidate full name |
| `email` | VARCHAR(255) | NOT NULL, INDEXED | Candidate email address |
| `phone` | VARCHAR(50) | NULLABLE | Candidate phone number |
| `resume_file_path` | VARCHAR(500) | NULLABLE | Path to uploaded resume file |
| `resume_text` | TEXT | NULLABLE | Extracted resume text content |
| `role_applied_for` | VARCHAR(255) | NULLABLE, INDEXED | Job role candidate applied for |
| `skills_extracted` | JSON | NULLABLE | AI-extracted skills list |
| `experience_depth` | VARCHAR(50) | NULLABLE | AI evaluation: Junior/Mid/Senior/Expert |
| `execution_evidence` | TEXT | NULLABLE | AI-extracted evidence of execution |
| `red_flags` | JSON | NULLABLE | AI-identified red flags list |
| `fit_score` | INTEGER | NULLABLE, INDEXED | AI-calculated fit score (0-100) |
| `executive_summary` | TEXT | NULLABLE | AI-generated 2-3 line candidate overview |
| `strengths` | TEXT | NULLABLE | AI-identified candidate strengths |
| `gaps` | TEXT | NULLABLE | AI-identified skill/experience gaps |
| `verdict` | VARCHAR(50) | NULLABLE, INDEXED | AI verdict: Strong Yes/Maybe/Reject/Better fit elsewhere |
| `status` | VARCHAR(50) | NOT NULL, DEFAULT 'screening', INDEXED | Pipeline status: screening/shortlisted/interview/offer/rejected |
| `interview_scheduled_at` | TIMESTAMP WITH TIME ZONE | NULLABLE | Scheduled interview date/time |
| `interview_kit` | JSON | NULLABLE | AI-generated interview questions, tasks, focus areas |
| `interview_feedback` | TEXT | NULLABLE | Human interviewer feedback |
| `evaluation_metadata` | JSON | NULLABLE | Full AI evaluation response |
| `created_at` | TIMESTAMP WITH TIME ZONE | NOT NULL, DEFAULT now(), INDEXED | Record creation timestamp |
| `updated_at` | TIMESTAMP WITH TIME ZONE | NOT NULL, DEFAULT now() | Record update timestamp |

**Relationships**:
- **Many-to-One** with `companies` (required)

**Indexes**:
- Primary key on `id`
- Foreign key index on `company_id`
- Index on `email` for candidate lookups
- Index on `role_applied_for` for role-based filtering
- Index on `fit_score` for sorting by quality
- Index on `verdict` for filtering by decision
- Index on `status` for pipeline filtering
- Index on `created_at` for time-based queries

**Notes**:
- **AI-Powered Evaluation**: Multiple fields populated by AI agents
- **Pipeline Tracking**: `status` tracks candidate through hiring stages
- **Interview Support**: `interview_kit` provides AI-generated interview materials
- **JSON Storage**: Skills, red flags, and evaluation metadata stored as JSON
- **Fit Scoring**: `fit_score` enables ranking candidates

**Business Rules**:
- Every candidate must belong to a company (multi-tenancy)
- Candidates progress through status pipeline: screening → shortlisted → interview → offer/rejected
- AI evaluation happens during screening stage
- Interview kit is generated when candidate is shortlisted

---

### 6. `audit_logs` Table

**Purpose**: Complete audit trail of all system actions

| Column Name | Data Type | Constraints | Description |
|-------------|-----------|-------------|-------------|
| `id` | UUID | PRIMARY KEY, NOT NULL, DEFAULT uuid_generate_v4() | Unique log identifier |
| `company_id` | UUID | FOREIGN KEY → companies.company_id, NULLABLE, INDEXED | Related company (if applicable) |
| `action_type` | VARCHAR(100) | NOT NULL, INDEXED | Action type: email_processed/draft_approved/company_added/etc |
| `action_description` | TEXT | NULLABLE | Human-readable action description |
| `source` | VARCHAR(255) | NULLABLE | Source of action (which template/snippet) |
| `template_used` | VARCHAR(255) | NULLABLE | Template name used (if applicable) |
| `approved_by` | UUID | NULLABLE | Admin ID who performed action |
| `approval_status` | VARCHAR(50) | NULLABLE | Approval status: approved/rejected/pending |
| `email_id` | UUID | NULLABLE, INDEXED | Related email ID (if applicable) |
| `draft_id` | UUID | NULLABLE, INDEXED | Related draft ID (if applicable) |
| `candidate_id` | UUID | NULLABLE, INDEXED | Related candidate ID (if applicable) |
| `extra_metadata` | JSON | NULLABLE | Additional context data |
| `created_at` | TIMESTAMP WITH TIME ZONE | NOT NULL, DEFAULT now(), INDEXED | Log creation timestamp |

**Relationships**:
- **Many-to-One** with `companies` (optional - some actions are system-wide)

**Indexes**:
- Primary key on `id`
- Foreign key index on `company_id`
- Index on `action_type` for filtering by action
- Index on `email_id` for email-related logs
- Index on `draft_id` for draft-related logs
- Index on `candidate_id` for candidate-related logs
- Index on `created_at` for time-based queries

**Notes**:
- **Complete Audit Trail**: Every significant action is logged
- **Optional Company Link**: Some actions (like admin login) don't belong to a company
- **Flexible Metadata**: `extra_metadata` JSON field stores additional context
- **Action Types**: Standardized action types for filtering and reporting

**Business Rules**:
- All system actions should be logged
- Company link is optional (system-wide actions don't need company)
- Logs are never deleted (immutable audit trail)

---

## Relationships Diagram

```
┌─────────────────┐
│     admins      │
│  (standalone)   │
└─────────────────┘

┌─────────────────────────────────────────────────────────┐
│                    companies                           │
│  ┌──────────────────────────────────────────────────┐  │
│  │ company_id (PK)                                  │  │
│  │ name (UNIQUE)                                    │  │
│  │ email (UNIQUE)                                   │  │
│  │ encrypted_access_token                           │  │
│  │ encrypted_refresh_token                          │  │
│  │ n8n_credential_id                                │  │
│  └──────────────────────────────────────────────────┘  │
└─────────────────────────────────────────────────────────┘
         │                    │                    │                    │
         │ 1                 │ 1                 │ 1                 │ 1
         │                    │                    │                    │
         │ *                 │ *                 │ *                 │ *
         ▼                    ▼                    ▼                    ▼
┌─────────────────┐  ┌─────────────────┐  ┌─────────────────┐  ┌─────────────────┐
│     emails      │  │     drafts     │  │   candidates    │  │  audit_logs    │
│                 │  │                 │  │                 │  │                 │
│ id (PK)         │  │ id (PK)        │  │ id (PK)         │  │ id (PK)         │
│ company_id (FK) │  │ company_id(FK) │  │ company_id (FK) │  │ company_id (FK)│
│ email_id (FK)   │  │                 │  │                 │  │                 │
│                 │  │                 │  │                 │  │                 │
│                 │  │                 │  │                 │  │                 │
└─────────────────┘  └─────────────────┘  └─────────────────┘  └─────────────────┘
         │                    │
         │ 1                 │ *
         │                    │
         ▼                    ▼
┌─────────────────┐  ┌─────────────────┐
│     drafts      │  │     drafts      │
│  (inbound)      │  │  (outbound)     │
│  email_id set   │  │  email_id null │
└─────────────────┘  └─────────────────┘
```

### Relationship Details

1. **companies → emails** (One-to-Many)
   - Cascade: DELETE
   - Every email belongs to exactly one company
   - Deleting a company deletes all its emails

2. **companies → drafts** (One-to-Many)
   - Cascade: DELETE
   - Every draft belongs to exactly one company
   - Deleting a company deletes all its drafts

3. **companies → candidates** (One-to-Many)
   - Cascade: DELETE
   - Every candidate belongs to exactly one company
   - Deleting a company deletes all its candidates

4. **companies → audit_logs** (One-to-Many, Optional)
   - Cascade: DELETE
   - Most logs belong to a company, but system-wide actions may not
   - `company_id` is nullable

5. **emails → drafts** (One-to-Many, Optional)
   - Cascade: DELETE
   - Drafts can be linked to an email (for inbound responses)
   - `email_id` is nullable (for outbound drafts)

---

## Indexes and Constraints

### Primary Keys
All tables use UUID v4 as primary keys:
- `admins.id`
- `companies.company_id`
- `emails.id`
- `drafts.id`
- `candidates.id`
- `audit_logs.id`

### Foreign Keys
- `emails.company_id` → `companies.company_id`
- `drafts.company_id` → `companies.company_id`
- `drafts.email_id` → `emails.id`
- `candidates.company_id` → `companies.company_id`
- `audit_logs.company_id` → `companies.company_id`

### Unique Constraints
- `admins.email` (unique)
- `companies.name` (unique)
- `companies.email` (unique)
- `emails.gmail_message_id` (unique, nullable)

### Indexes Summary

**Performance Indexes**:
- All foreign keys are indexed
- All unique columns are indexed
- Frequently queried columns are indexed:
  - `companies.status`
  - `emails.priority_score`
  - `emails.created_at`
  - `drafts.status`
  - `candidates.status`
  - `candidates.fit_score`
  - `audit_logs.action_type`
  - `audit_logs.created_at`

**Composite Indexes**: None (consider adding if query patterns require)

---

## Data Flow

### 1. Company Registration Flow

```
1. Admin creates company (name, email)
   → INSERT INTO companies (name, email, status='active')
   → company_id generated

2. Company connects OAuth
   → UPDATE companies SET 
        encrypted_access_token = ?,
        encrypted_refresh_token = ?,
        n8n_credential_id = ?
   → OAuth tokens encrypted before storage
```

### 2. Inbound Email Processing Flow

```
1. n8n detects new email in company inbox
   → Calls backend: POST /api/emails/process

2. Backend creates email record
   → INSERT INTO emails (
        company_id,
        subject,
        body,
        from_email,
        to_email,
        gmail_message_id
     )

3. AI Agents process email
   → Classification Agent → UPDATE emails SET function, intent, urgency, impact
   → Priority Agent → UPDATE emails SET priority_score
   → Summary Agent → UPDATE emails SET executive_summary
   → Action Agent → UPDATE emails SET recommended_action

4. Draft generation (if action = "Reply")
   → INSERT INTO drafts (
        company_id,
        email_id,
        subject,
        body,
        status='pending'
     )

5. Human approves draft
   → UPDATE drafts SET 
        status='approved',
        approved_by=admin_id,
        approved_at=now()

6. Draft sent
   → UPDATE drafts SET 
        status='sent',
        sent_at=now()
   → INSERT INTO audit_logs (action_type='draft_sent', draft_id=?)

7. Audit logging
   → INSERT INTO audit_logs (
        company_id,
        action_type='email_processed',
        email_id=?,
        extra_metadata={...}
     )
```

### 3. Candidate Hiring Flow

```
1. Resume received (email/upload)
   → INSERT INTO candidates (
        company_id,
        name,
        email,
        resume_text,
        status='screening'
     )

2. AI Evaluation
   → Skills Agent → UPDATE candidates SET skills_extracted
   → Evaluation Agent → UPDATE candidates SET 
        fit_score,
        strengths,
        gaps,
        verdict

3. Summary Agent
   → UPDATE candidates SET executive_summary

4. Human decision: Shortlist
   → UPDATE candidates SET status='shortlisted'

5. Interview kit generation
   → UPDATE candidates SET interview_kit={...}

6. Interview scheduled
   → UPDATE candidates SET interview_scheduled_at=?

7. Interview feedback
   → UPDATE candidates SET 
        interview_feedback=?,
        status='interview'

8. Final decision
   → UPDATE candidates SET 
        verdict=?,
        status='offer' OR 'rejected'
   → INSERT INTO audit_logs (action_type='candidate_decision', candidate_id=?)
```

---

## Multi-Tenancy Architecture

### Data Isolation

All business data is isolated by `company_id`:
- **emails**: Filtered by `company_id`
- **drafts**: Filtered by `company_id`
- **candidates**: Filtered by `company_id`
- **audit_logs**: Filtered by `company_id` (when applicable)

### Query Pattern

All queries must include `company_id` filter:

```sql
-- ✅ Correct: Multi-tenant query
SELECT * FROM emails WHERE company_id = ? AND priority_score > 50;

-- ❌ Wrong: Missing company_id (security risk)
SELECT * FROM emails WHERE priority_score > 50;
```

### Cross-Company Queries

Some queries aggregate across companies (for admin dashboard):
- Priority queue (all companies, sorted by priority_score)
- Hiring pipeline overview (all companies)
- System-wide audit logs

---

## Security Considerations

### Encryption

1. **OAuth Tokens**: 
   - `encrypted_access_token` and `encrypted_refresh_token` are encrypted before storage
   - Encryption key stored in environment variables
   - Tokens are decrypted only when needed for API calls

2. **Passwords**:
   - `encrypted_password` in `admins` table is hashed (not encrypted)
   - Uses secure hashing algorithm (bcrypt/argon2)

### Data Access

1. **Foreign Key Constraints**: Ensure referential integrity
2. **Cascade Deletes**: Prevent orphaned records
3. **Unique Constraints**: Prevent duplicate companies/emails
4. **Indexes**: Ensure fast queries with proper isolation

---

## Migration History

### Key Migrations

1. **Token Fields Nullable** (`migrate_token_fields_nullable.py`)
   - Made OAuth token fields nullable to support two-step registration
   - Allows companies to exist without OAuth initially

2. **Unique Name Constraint** (`migrate_add_unique_name_constraint.py`)
   - Added unique constraint on `companies.name`
   - Prevents duplicate company names

3. **Initial Schema** (`init_db.py`)
   - Creates all tables with proper relationships
   - Sets up indexes and constraints

---

## Future Considerations

### Potential Enhancements

1. **Composite Indexes**: 
   - `(company_id, priority_score)` on `emails` for faster queue queries
   - `(company_id, status)` on `candidates` for pipeline filtering

2. **Partitioning**:
   - Consider partitioning `emails` and `audit_logs` by `created_at` for large datasets

3. **Full-Text Search**:
   - Add full-text search indexes on `emails.body` and `candidates.resume_text`

4. **Soft Deletes**:
   - Add `deleted_at` column to support soft deletes instead of cascade deletes

5. **Archiving**:
   - Consider archiving old emails and audit logs to separate tables

---

## Database Connection

### Connection String Format

```
postgresql+asyncpg://user:password@host:port/database
```

### Connection Pool Settings

- **Pool Size**: Default (5 connections)
- **Max Overflow**: 10 connections
- **Pool Recycle**: 3600 seconds (1 hour)
- **Pool Timeout**: 10 seconds
- **Connection Timeout**: 10 seconds

### Environment Variables

- `DATABASE_URL`: Async connection string
- `DATABASE_URL_SYNC`: Sync connection string (for migrations)

---

## Summary

This database structure supports:

✅ **Multi-tenancy** with company-based data isolation  
✅ **AI-powered email processing** with classification and prioritization  
✅ **Hiring pipeline management** with candidate evaluation  
✅ **Complete audit trail** of all system actions  
✅ **Two-step company registration** with optional OAuth  
✅ **Human-in-the-loop** draft approval workflow  
✅ **Scalable architecture** with proper indexes and constraints  

The schema is designed to support the **S Combinator Central Agent Platform** blueprint for customer acquisition and hiring automation.

---

**Last Updated**: 2026-02-06  
**Database Version**: PostgreSQL (version compatible)  
**ORM**: SQLAlchemy (Async)

