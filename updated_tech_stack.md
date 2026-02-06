# S Combinator Platform -- Updated Tech Stack Summary

## 1. Backend & AI Layer

-   FastAPI
-   Python 3.11+
-   OpenAI (GPT Models)
-   LangGraph
-   LangChain
-   LangSmith

## 2. Database & Caching

-   PostgreSQL 15+
-   Redis
-   SQLAlchemy 2.0
-   asyncpg
-   Alembic

## 3. Workflow Orchestration

-   n8n (Self-hosted using Docker / Node.js)
-   Gmail / Drive APIs
-   n8n Scheduler

## 4. Frontend (User Interface)

-   React 18
-   TypeScript
-   Tailwind CSS
-   shadcn/ui / MUI
-   React Query
-   Zustand
-   Vite
-   React Router v6

## 5. Authentication & Security

-   JWT
-   Google OAuth 2.0
-   bcrypt
-   python-jose
-   AES / KMS / Vault

## 6. Development Environment

-   Python venv uv 
-   npm / yarn
-   Swagger

## 7. Overall Architecture Summary

  Layer        Technology Used          Role
  ------------ ------------------------ ------------------
  UI Layer     React + TS               User Interface
  API Layer    FastAPI                  Request Handling
  AI Layer     LangGraph + OpenAI       AI Processing
  Workflow     n8n (Docker / Node.js)   Automation
  Data Layer   PostgreSQL + Redis       Storage

------------------------------------------------------------------------

