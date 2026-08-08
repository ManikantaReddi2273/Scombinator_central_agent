# S Combinator Central Agent Platform  
## Summer Internship Project — Presentation Source Document

> **How to use this file:** Give this entire markdown to Claude (or another AI) and ask it to generate a PowerPoint using these sections as slides.  
> Keep ~1–2 slides per major heading unless noted.

---

### Suggested slide metadata (for PPT generator)

| Field | Value |
|-------|--------|
| **Project title** | S Combinator — Central Agent Platform |
| **Subtitle** | Multi-Company AI Email Operations for Customer Acquisition |
| **Type** | Summer Internship Project |
| **Focus** | AI agents, LangGraph pipelines, human-in-the-loop automation |
| **Stack** | FastAPI, React, LangGraph, OpenAI, n8n, PostgreSQL, Gmail/Drive |
| **Tone** | Professional, internship defense / tech presentation |
| **Visual style** | Clean corporate; architecture diagrams; flow arrows; avoid clutter |

---

# 1. Title Slide

**S Combinator — Central Agent Platform**

*Multi-Company AI Agent Platform for Automated Customer Acquisition Email Operations*

- Summer Internship Project  
- Domain: Generative AI · Multi-Agent Systems · Workflow Automation  
- Human-in-the-loop design (AI drafts → human approves → send)

**Optional line:**  
*Parent company + spin-offs · Unified priority queue · On-brand drafts*

---

# 2. Problem Statement

## The business problem

Growing organizations (a parent company and multiple spin-offs) manage **many Gmail inboxes** and CRM pipelines at once. Email operations become:

- **Overloaded** — high volume of inbound sales, support, hiring, and partner mail  
- **Inconsistent** — replies differ by person and brand; tone drifts  
- **Slow** — important revenue or hiring messages get buried  
- **Manual** — B2B/B2C follow-ups depend on memory and spreadsheets  
- **Fragmented** — no single priority view across companies  

## Core pain points

1. No shared **cross-company priority queue** for inbound email  
2. Classification of function / intent / urgency is done mentally (error-prone)  
3. Drafting on-brand replies is time-consuming  
4. Outbound CRM follow-ups (B2B LEADS / B2C funnel) are easy to miss  
5. Full auto-send without review creates **brand and compliance risk**

## Problem statement (one sentence)

> *How can a multi-company organization automate understanding, prioritization, and drafting of customer-acquisition emails—while keeping a human in control before anything is sent?*

---

# 3. Objectives

## Primary objectives

1. Build a **central agent platform** that serves multiple companies (tenants) from one admin dashboard  
2. Automate **inbound email understanding** (classify → score → summarize → recommend → draft)  
3. Automate **outbound follow-up drafting** from CRM (B2B and B2C)  
4. Enforce **human-in-the-loop approval** before any email is sent  
5. Integrate with **Gmail, Google Drive, and Google Sheets** as the operational source of truth  

## Secondary objectives

6. Provide a unified **Priority Queue** and **Drafts** workspace for admins  
7. Keep each company’s **brand context** (voice, policies, templates) in drafts  
8. Log outcomes for auditability  
9. Deploy a working stack (backend + frontend; n8n for scheduled automation)  
10. Document architecture and flows for handover / presentation  

## Success criteria

| Criterion | Target |
|-----------|--------|
| Multi-tenant companies | Add company → connect OAuth → isolated data |
| Inbound Flow 1 | Email → AI draft appears in dashboard |
| Outbound Flow 2 | Lead → outbound draft from CRM context |
| Safety | No send without approval path |
| Ops | Admin can review, edit, approve/reject drafts |

---

# 4. Proposed Approach

## Design principle

```
Raw input
  → Structured understanding
  → Prioritized decision
  → Editable AI draft
  → Human approval
  → Logged outcome
```

## Solution approach (high level)

| Layer | Approach |
|-------|----------|
| **Ingestion** | n8n polls Gmail for connected companies and posts emails to the backend |
| **Intelligence** | LangGraph multi-step AI pipeline (OpenAI) for inbound and outbound |
| **Persistence** | PostgreSQL stores companies, emails, drafts, audit logs |
| **Control plane** | React admin dashboard for queue, drafts, companies, B2B/B2C |
| **Actuation** | After approval, n8n sends via Gmail and can update CRM |
| **Safety** | Explicit approve/reject; AI never silently sends |

## Scope delivered in internship

| Area | Status |
|------|--------|
| Flow 1 — Inbound → draft | Implemented |
| Flow 2 — Outbound B2B/B2C drafts | Implemented |
| Multi-company OAuth + dashboard | Implemented |
| Human approval before send | Implemented |
| Flow 3/4 — Hiring agents | Blueprint only (future) |

## Why this approach (vs alternatives)

- **vs single chatbot reply:** Multi-step structured pipeline is more reliable for ops  
- **vs full auto-send:** Human approval protects brand  
- **vs one inbox tool:** Multi-tenant model fits parent + spin-offs  
- **vs custom cron scripts:** n8n gives visible, editable workflows  

---

# 5. System Architecture

## High-level architecture

```
┌──────────────────┐      ┌─────────────────────────┐      ┌──────────────┐
│  React Frontend  │─────▶│  FastAPI Backend         │─────▶│  PostgreSQL  │
│  Admin Dashboard │      │  LangGraph + OpenAI      │      │  Tenants,    │
└──────────────────┘      └───────────┬─────────────┘      │  Emails,     │
                                      │                    │  Drafts      │
                     ┌────────────────┼────────────────┐   └──────────────┘
                     ▼                ▼                ▼
               ┌──────────┐   ┌──────────┐   ┌────────────────┐
               │   n8n    │   │  Gmail   │   │ Drive / Sheets │
               │ Schedule │   │ Read/Send│   │ CRM + Brand    │
               └──────────┘   └──────────┘   └────────────────┘
```

## Component responsibilities

| Component | Responsibility |
|-----------|----------------|
| **Frontend (React)** | Login, Priority Queue, Drafts, Emails, B2B/B2C, Companies |
| **Backend (FastAPI)** | APIs, auth, tenant mapping, AI orchestration, token storage |
| **LangGraph + OpenAI** | Multi-agent / multi-node email pipelines |
| **PostgreSQL** | System of record for platform data |
| **n8n** | Scheduled Gmail poll, send approved drafts, follow-up cron |
| **Google APIs** | Gmail, Drive brand docs, Sheets CRM (LEADS / B2C_FUNNEL) |

## Multi-tenant model

- Each **company** = tenant (own Gmail OAuth tokens, Drive CRM, emails, drafts)  
- Tokens stored **encrypted** (Fernet)  
- Admin sees **all companies** in one unified priority queue  

## Request path examples

1. **Inbound:** Gmail → n8n → `POST /api/emails/process` → Flow 1 → DB → Dashboard  
2. **Outbound:** UI/n8n → `POST /api/outbound/create` → Flow 2 → Draft → Approve → Send  
3. **OAuth:** Dashboard → Google → Backend callback → encrypted tokens on company  

## Deployment topology (typical)

- Frontend + Backend + Postgres on **Render**  
- n8n on **local Docker** (or hosted n8n for always-on automation)  

---

# 6. Multi-Agent Pipeline

> In this project, “multi-agent” is realized as a **LangGraph multi-node pipeline** where each node is a specialized AI step with a clear responsibility.

## Flow 1 — Inbound Email → Response (Customer Acquisition)

| Step / Node | Role | Output |
|-------------|------|--------|
| **1. Ingestion** | Map inbox → company; capture thread | Tenant + thread context |
| **2. Classification agent** | Multi-dimensional understanding | Function, Intent, Urgency, Impact, Confidence |
| **3. Priority scorer** | Convert signals → score | Priority 0–100; queue order |
| **4. Summarizer** | Executive meaning (not a quote) | 1–2 line summary |
| **5. Action recommender** | Suggest next best action | Reply / ask info / schedule / escalate / hold… |
| **6. Draft generator** | On-brand reply using Drive brand context | Editable draft subject + body |
| **7. Human review** | Admin edits / approves / rejects | Approved draft ready to send |
| **8. Send & log** | n8n sends via Gmail; audit/CRM update | Sent mail + logs |

### Classification dimensions (Flow 1)

| Dimension | Examples |
|-----------|----------|
| Function | Sales, Hiring, Legal, Support, Ops, Marketing, Admin |
| Intent | Inquiry, Follow-up, Objection, Scheduling, Application, FAQ, Complaint |
| Urgency | Immediate, Soon, Can wait |
| Impact | Revenue, Hiring-critical, Brand-sensitive, Low |
| Confidence | Clear, Ambiguous, Missing information |

### Flow 1 visual (for slide)

```
Email → Classify → Score → Summarize → Recommend → Draft → Human Approve → Send
```

## Flow 2 — Outbound Email → Draft (B2B / B2C)

| Step | Role |
|------|------|
| Trigger | Manual UI **or** n8n schedule (leads due for follow-up) |
| Intent | Decide outreach goal (follow-up, meeting, proposal, objection…) |
| Recipient context | Load CRM lead fields from Sheets |
| Template / brand | Company voice + templates from Drive |
| Draft | Generate outbound email draft |
| Human approve | Same approval gate as inbound |
| Send + CRM | n8n sends; update activity / next follow-up |

### Outbound types

| Type | CRM sheet | Use case |
|------|-----------|----------|
| **B2B** | `LEADS` | Institutions, demos, proposals |
| **B2C** | `B2C_FUNNEL` | Campaign / social commenter follow-ups |

## Orchestration notes (implementation)

- Orchestrators: `flow1/orchestrator.py`, `flow2/orchestrator.py`  
- Nodes under `backend/services/flow1/nodes/` and Flow 2 equivalents  
- On hosted free tiers, `/api/emails/process` may **accept quickly (HTTP 202)** and run AI **in background** to avoid gateway timeouts  

## Safety agent principle

- Draft generation ≠ send permission  
- **Human is the final agent** in the control loop  

---

# 7. Key Features

## Product features

1. **Multi-company management** — Add, connect Gmail/Drive, delete company (cascade related data)  
2. **OAuth-connected inboxes** — Per-company Gmail tokens (encrypted)  
3. **Inbound AI processing (Flow 1)** — Classify, score, summarize, recommend, draft  
4. **Unified Priority Queue** — Cross-company view sorted by AI priority  
5. **Drafts workspace** — Review, edit, approve, reject  
6. **B2B Outbound** — CRM LEADS → create outbound drafts  
7. **B2C Outreach** — CRM B2C_FUNNEL → create outbound drafts  
8. **Brand-aware drafting** — Uses company docs from Google Drive  
9. **Scheduled automation (n8n)** — Email ingestion, send approved drafts, follow-up crons  
10. **Human-in-the-loop** — Mandatory approval before send  
11. **Audit-oriented logging** — Actions tracked for accountability  
12. **Cloud-ready deploy** — Render Blueprint for frontend/backend/DB  

## Dashboard modules

| Module | Feature |
|--------|---------|
| Dashboard | High-level stats |
| Priority Queue | Urgent work first |
| Drafts | Approval gate |
| Emails | Processed mail history |
| B2B / B2C | Lead-driven outreach |
| Companies | Tenant + OAuth + delete |

## Differentiators

- Multi-tenant **central** agent (not single-inbox gadget)  
- Structured multi-step AI (not one-shot reply)  
- CRM + brand docs in the loop  
- Explicit human control for send  

---

# 8. Technology Stack

## Stack table (for PPT)

| Layer | Technologies |
|-------|----------------|
| Frontend | React 18, TypeScript, Vite, Tailwind CSS, React Query, Zustand, Axios |
| Backend | Python 3.10+, FastAPI, Uvicorn, Pydantic, SQLAlchemy 2 (async), asyncpg |
| AI / Agents | LangGraph, LangChain, OpenAI GPT-4o |
| Database | PostgreSQL 15+ |
| Cache | Redis (optional brand-context cache) |
| Automation | n8n (Docker) |
| Integrations | Gmail API, Google Drive API, Google Sheets API |
| Auth & security | JWT, bcrypt, Fernet encryption for OAuth tokens |
| Deploy | Render (Blueprint / `render.yaml`) |

## Why these choices (short talking points)

- **FastAPI** — fast async APIs, clear OpenAPI docs for internship demos  
- **LangGraph** — explicit multi-step agent graphs (better than unstructured prompts)  
- **React + Vite** — modern admin UI, quick iteration  
- **PostgreSQL** — reliable multi-tenant relational store  
- **n8n** — low-code ops for Gmail schedules without rewriting cron glue  
- **OpenAI** — high-quality classification and drafting  
- **Human approval** — practical enterprise constraint  

---

# 9. Results & Discussion

## What was achieved

| Result | Description |
|--------|-------------|
| Working end-to-end Flow 1 | Inbox email → AI draft in Priority Queue / Drafts |
| Working Flow 2 | B2B/B2C leads → outbound drafts from CRM context |
| Multi-tenant platform | Multiple companies with isolated OAuth and data |
| Admin control | Approve/reject/edit before send |
| Automation layer | n8n workflows for ingestion and sending |
| Deployable system | Frontend/backend hosted; documented local + cloud setup |

## Observed behavior / learnings

1. **Human-in-the-loop is essential** for brand-safe automation  
2. **Structured pipelines outperform** one-shot “write a reply” prompts for ops  
3. **Multi-tenant complexity** (tokens, CRM folders, brand docs) is the real product challenge—not just the LLM call  
4. **Free cloud hosting** introduces cold starts / timeouts; engineering must design for async accept + background AI  
5. **Gmail rate limits** require sequential/batched API calls in workflows  
6. **n8n + backend split** clarifies roles: automation vs intelligence  

## Challenges faced & how addressed

| Challenge | Mitigation |
|-----------|------------|
| Long AI requests timing out on free hosting | Accept email quickly (202) + background processing |
| Parallel Flow 1 overloading free tier | Serialize AI jobs; limit emails per n8n run |
| OAuth without public n8n | Backend OAuth callback on Render |
| Gmail “too many concurrent requests” | Batch size 1 + retries + continue-on-fail |
| Missing drafts for some actions | Broaden draft persistence for reply-worthy actions |
| Env/venv confusion in local setup | Document `.venv` and run order clearly |

## Discussion (internship angle)

- Demonstrates practical GenAI engineering: **orchestration, integrations, tenancy, UX, deploy**  
- Shows understanding that production AI is a **system**, not a prompt  
- Leaves clear extension path (hiring flows, hosted n8n, evaluation metrics)  

---

# 10. Conclusion & Future Scope

## Conclusion

The internship delivered a **working Central Agent Platform** that:

- Serves **multiple companies** from one control plane  
- Uses a **multi-node LangGraph pipeline** to understand and draft inbound/outbound customer-acquisition emails  
- Integrates **Gmail + Drive + Sheets CRM**  
- Keeps a **human approval gate** before send  

This validates that AI can accelerate email ops **without removing human accountability**.

## Future scope

| Priority | Future work |
|----------|-------------|
| High | Implement **Hiring Flows 3 & 4** from the blueprint |
| High | Host **always-on n8n** (or equivalent) for production schedules |
| Medium | Draft quality evaluation (human ratings, A/B tone checks) |
| Medium | Stronger analytics dashboard (SLA, conversion, time-to-reply) |
| Medium | Role-based access (per-company managers, not only global admin) |
| Low | Slack/Teams notifications for high-priority emails |
| Low | Multilingual drafting; attachment understanding |
| Low | Deeper CRM write-backs and sequence automation |

## Closing statement (for last slide)

> *S Combinator Central Agent Platform shows how multi-agent AI pipelines, workflow automation, and human-in-the-loop design can turn chaotic multi-inbox email operations into a prioritized, brand-safe, and scalable system.*

---

# 11. References

## Technical documentation & libraries

1. FastAPI Documentation — https://fastapi.tiangolo.com/  
2. LangGraph Documentation — https://langchain-ai.github.io/langgraph/  
3. LangChain Documentation — https://python.langchain.com/  
4. OpenAI API Documentation — https://platform.openai.com/docs  
5. React Documentation — https://react.dev/  
6. Vite Documentation — https://vitejs.dev/  
7. SQLAlchemy 2.0 Documentation — https://docs.sqlalchemy.org/  
8. PostgreSQL Documentation — https://www.postgresql.org/docs/  
9. n8n Documentation — https://docs.n8n.io/  
10. Google Gmail API — https://developers.google.com/gmail/api  
11. Google Drive API — https://developers.google.com/drive  
12. Google Sheets API — https://developers.google.com/sheets  
13. Render Documentation — https://render.com/docs  

## Project / domain references

14. Project blueprint: *S Combinator — Central Agent Platform (Customer Acquisition and Hiring)* (internal blueprint document)  
15. Project README & architecture notes (repository)  
16. Project flow diagram: `PROJECT_FLOW.mmd`  
17. Outbound use-case notes (repository)  

## Concepts (optional academic / industry framing)

18. Human-in-the-loop machine learning / AI systems (industry practice)  
19. Multi-agent / agentic workflow design patterns (LangGraph-style orchestration)  
20. Multi-tenant SaaS architecture patterns  

---

# Appendix A — Suggested PPT slide order (for Claude)

Use roughly **12–16 slides**:

1. Title  
2. Agenda  
3. Problem Statement  
4. Objectives  
5. Proposed Approach  
6. System Architecture (diagram)  
7. Multi-Agent Pipeline — Flow 1  
8. Multi-Agent Pipeline — Flow 2  
9. Key Features  
10. Technology Stack  
11. Results & Discussion  
12. Challenges & Mitigations  
13. Conclusion  
14. Future Scope  
15. References  
16. Thank You / Q&A  

---

# Appendix B — Speaker notes (short)

- Emphasize **human approval** as a product feature, not a limitation.  
- Emphasize **multi-company** as the “Central” in Central Agent Platform.  
- Flow 1 = someone emails you; Flow 2 = you email leads.  
- n8n = hands/schedule; LangGraph = brain; React = control room.  
- Hiring flows are designed but not coded — honest internship scope.

---

# Appendix C — One-line elevator pitch

> *We built a multi-tenant AI platform that reads company inboxes and CRM leads, runs a LangGraph agent pipeline to prioritize and draft emails, and lets humans approve before Gmail sends—so a parent company and its spin-offs share one intelligent email operations center.*

---

*End of presentation source document.*
