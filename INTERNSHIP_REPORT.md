# Summer Internship Report

# S Combinator — Central Agent Platform  
### Multi-Company AI Email Operations for Customer Acquisition

**Department of CSE**  
**Summer Internship Report**

> This document follows a standard internship-report structure (similar to peer reports).  
> Sections that do not apply to this project (e.g. finance ledgers, Instagram DM, mobile apps) are omitted.

---

## Contents

| | Topic | |
|---|--------|---|
| | Acknowledgement | |
| | Abstract | |
| **1** | **Introduction** | |
| 1.1 | About S Combinator and the Platform Context | |
| 1.2 | Internship Overview | |
| 1.3 | My Role and Contribution | |
| 1.4 | Problem Statement | |
| 1.5 | Objectives | |
| 1.6 | Scope of this Report | |
| **2** | **System Architecture Overview** | |
| 2.1 | Overall Platform Architecture | |
| 2.2 | Shared Infrastructure and Components | |
| 2.3 | Technology Stack Summary | |
| **3** | **Flow 1: Inbound Email → Response Pipeline** | |
| 3.1 | Module Overview | |
| 3.2 | Email Ingestion and Company Identification | |
| 3.3 | Multi-Dimensional Classification | |
| 3.4 | Priority Scoring and Unified Queue | |
| 3.5 | Executive Summary and Action Recommendation | |
| 3.6 | Brand-Aware Draft Generation | |
| 3.7 | Human Review, Send, and Logging | |
| 3.8 | Why This Counts as Multi-Agent / Agentic Automation | |
| **4** | **Flow 2: Outbound B2B / B2C Drafting** | |
| 4.1 | Module Overview | |
| 4.2 | B2B Outbound (LEADS) | |
| 4.3 | B2C Outreach (B2C_FUNNEL) | |
| 4.4 | CRM Integration via Google Sheets | |
| **5** | **Admin Dashboard and Multi-Tenant Management** | |
| 5.1 | Dashboard Modules | |
| 5.2 | Company Onboarding and OAuth | |
| 5.3 | Draft Approval Workspace | |
| **6** | **n8n Automation Layer** | |
| 6.1 | Role of n8n in the System | |
| 6.2 | Key Workflows | |
| 6.3 | Known Limitations | |
| **7** | **Results and Evaluation** | |
| 7.1 | Feature Completion Summary | |
| 7.2 | Before vs After | |
| 7.3 | Challenges Faced and Resolved | |
| 7.4 | Honest Limitations Summary | |
| **8** | **Conclusion and Future Scope** | |
| 8.1 | Conclusion | |
| 8.2 | Future Scope | |
| | References | |

---

# Acknowledgement

I express my sincere gratitude to everyone who supported me during this summer internship.

I thank my internship mentors and the team associated with the **S Combinator Central Agent Platform** initiative for giving me the opportunity to work on a real multi-tenant AI systems problem involving email operations, agent orchestration, and product engineering.

I am grateful to the **Department of Computer Science and Engineering** for enabling this internship and for academic guidance throughout the process.

I also thank my peers and seniors for discussions that helped refine the architecture, documentation, and presentation of this work.

Finally, I thank my family for their continuous support during the internship period.

---

# Abstract

This report presents the design and implementation work carried out during the summer internship on the **S Combinator — Central Agent Platform**, a multi-company AI system for **customer-acquisition email operations**.

Organizations that operate a parent company and multiple spin-offs typically manage several Gmail inboxes and CRM pipelines in parallel. Email handling becomes fragmented, slow, and inconsistent, while fully automated sending without review introduces brand and compliance risk.

The platform addresses this by combining:

1. **Workflow automation (n8n)** to poll Gmail and send approved messages  
2. **LangGraph multi-node AI pipelines (OpenAI)** to classify, prioritize, summarize, recommend actions, and draft emails  
3. **A React admin dashboard** for a unified priority queue and human approval  
4. **PostgreSQL multi-tenant storage** with encrypted Google OAuth tokens  
5. **Google Drive / Sheets** for brand context and B2B/B2C CRM data  

Two major operational flows were implemented:

- **Flow 1 (Inbound):** email → understand → prioritize → draft → human approve → send  
- **Flow 2 (Outbound):** CRM lead → context-aware draft → human approve → send  

Hiring-related flows from the product blueprint remain future work. The internship demonstrates practical generative-AI engineering: orchestration, integrations, tenancy, human-in-the-loop safety, and deployment—not only prompt writing.

**Keywords:** Multi-agent systems, LangGraph, FastAPI, React, n8n, Gmail API, multi-tenant SaaS, human-in-the-loop AI, customer acquisition automation

---

# 1 Introduction

## 1.1 About S Combinator and the Platform Context

**S Combinator Central Agent Platform** is conceived as a shared operational layer for a **parent organization and its spin-off companies**. Each company has its own brand identity, Gmail inbox, CRM sheets, and tone of communication, but leadership still needs one place to see what matters most across the group.

The platform’s design principle is:

> Convert raw inputs → structured understanding → prioritized decisions → editable drafts → logged outcomes — with a human always in control before send.

The product focus for this internship phase is **Part A — Customer Acquisition** (inbound replies and outbound follow-ups). Hiring automation is specified in the blueprint but was outside the implementation scope of this internship.

## 1.2 Internship Overview

| Item | Description |
|------|-------------|
| Project | S Combinator — Central Agent Platform |
| Domain | Generative AI, multi-agent pipelines, workflow automation |
| Nature of work | Full-stack product engineering + AI orchestration |
| Major deliverables | Flow 1, Flow 2, multi-tenant dashboard, n8n workflows, docs/deploy notes |

The internship involved understanding the product blueprint, implementing backend AI pipelines, wiring Google integrations, building/using the admin UI flows, automating Gmail operations with n8n, and validating end-to-end behaviour (including cloud hosting constraints).

## 1.3 My Role and Contribution

During the internship I worked as a **full-stack / AI systems intern** on the central platform. Key contributions included:

- Understanding and documenting the **customer-acquisition flows** (inbound and outbound)  
- Working on / with the **Flow 1 LangGraph pipeline** (classification → scoring → summary → action → draft)  
- Supporting **Flow 2 outbound drafting** for B2B and B2C CRM leads  
- Helping integrate **Gmail OAuth**, token handling, and company tenancy concepts  
- Working with **n8n workflows** for email ingestion and approved-draft sending  
- Using the **React dashboard** for priority queue, drafts, companies, and outbound pages  
- Assisting with **deployment/documentation** (local run, Render hosting, operational caveats)  
- Preparing internship presentation and report material  

*(Adjust names/tools in this subsection to match exactly what you personally built vs. collaborated on before final submission.)*

## 1.4 Problem Statement

Growing multi-brand groups face operational email chaos:

1. **High volume** across many company inboxes  
2. **No shared priority view** — urgent revenue/hiring mail is easy to miss  
3. **Inconsistent replies** — tone and quality vary by person and brand  
4. **Manual CRM follow-ups** — B2B/B2C sequences depend on memory and spreadsheets  
5. **Unsafe full automation** — sending without review risks brand damage  

**Problem statement:**  
*How can a multi-company organization automate understanding, prioritization, and drafting of customer-acquisition emails across tenants, while enforcing human approval before any message is sent?*

## 1.5 Objectives

1. Build / advance a **central multi-tenant platform** for parent + spin-off companies  
2. Automate **inbound email intelligence and drafting** (Flow 1)  
3. Automate **outbound B2B/B2C draft creation** from CRM (Flow 2)  
4. Provide an admin **Priority Queue** and **Drafts** workspace  
5. Integrate **Gmail, Google Drive, and Google Sheets**  
6. Enforce **human-in-the-loop approval** before send  
7. Document architecture, flows, setup, and limitations for academic evaluation  

## 1.6 Scope of this Report

**In scope**

- Platform context and problem  
- Architecture and technology stack  
- Flow 1 inbound pipeline (deep dive)  
- Flow 2 outbound B2B/B2C  
- Dashboard / multi-tenant company management  
- n8n automation role  
- Results, challenges, limitations, future work  

**Out of scope (ignored from peer-report style modules that do not exist here)**

- Finance / accounting ledgers, tax, banking modules  
- Affiliate / Instagram DM marketing products  
- Mobile applications  
- Wrapper billing / credit-deduction platforms unrelated to this codebase  

**Future / blueprint only**

- Hiring Flows 3 and 4 (candidate screening / interview ops)

---

# 2 System Architecture Overview

## 2.1 Overall Platform Architecture

The system is organized into four cooperating layers:

```
┌────────────────────┐
│  React Admin UI    │  Control plane (queue, drafts, companies, outbound)
└─────────┬──────────┘
          │ REST / JWT
┌─────────▼──────────┐
│ FastAPI Backend    │  Tenancy, APIs, LangGraph AI orchestration
│ + OpenAI           │
└─────────┬──────────┘
          │
    ┌─────┴──────┬──────────────┐
    ▼            ▼              ▼
PostgreSQL     n8n           Google APIs
(emails,       (poll/send/   (Gmail, Drive,
 drafts,        schedules)    Sheets CRM)
 companies)
```

**Inbound path:** Gmail → n8n → `POST /api/emails/process` → Flow 1 → DB → Dashboard → Approve → n8n send  

**Outbound path:** Lead (UI or schedule) → `POST /api/outbound/create` → Flow 2 → Draft → Approve → send / CRM update  

## 2.2 Shared Infrastructure and Components

| Component | Role |
|-----------|------|
| **Companies (tenants)** | Identity, encrypted OAuth tokens, Drive folder linkage |
| **Emails** | Inbound/outbound records + classification metadata |
| **Drafts** | Pending / approved / rejected / sent AI drafts |
| **Brand context loader** | Reads company docs from Drive for on-brand drafting |
| **CRM loader** | Reads B2B/B2C sheets for outbound context |
| **Token manager** | Refreshes Gmail access tokens for n8n/backend use |
| **Audit logs** | Tracks important system actions |

Shared design rules:

- One admin control plane across companies  
- Data isolation by `company_id`  
- AI proposes; humans dispose (approve/reject)  

## 2.3 Technology Stack Summary

| Layer | Technologies |
|-------|----------------|
| Frontend | React 18, TypeScript, Vite, Tailwind CSS, React Query, Zustand |
| Backend | Python, FastAPI, Uvicorn, Pydantic, SQLAlchemy 2 (async), asyncpg |
| AI | LangGraph, LangChain, OpenAI (GPT-4o) |
| Database | PostgreSQL |
| Automation | n8n (Docker) |
| Integrations | Gmail API, Google Drive API, Google Sheets API |
| Security | JWT admin auth, Fernet-encrypted OAuth tokens, service API key for n8n |
| Deploy | Render (frontend + backend + Postgres); n8n typically local Docker |

---

# 3 Flow 1: Inbound Email → Response Pipeline

## 3.1 Module Overview

Flow 1 is the flagship customer-acquisition pipeline: **someone emails a company inbox and expects a response**.

The system does not merely “chat back.” It runs a structured multi-step pipeline so operators get:

- Structured classification  
- A numeric priority  
- A short executive summary  
- A recommended action  
- An editable draft in company brand voice  

## 3.2 Email Ingestion and Company Identification

1. n8n **Email Ingestion** workflow runs on a schedule  
2. Backend lists companies with OAuth connected  
3. For each company, a valid Gmail token is fetched  
4. Unread inbox messages are retrieved  
5. Message fields (subject, body, from, to, thread, Gmail ID) are extracted  
6. Backend `POST /api/emails/process` accepts the email (tenant mapped by company / credential / to-address)  
7. Duplicates are skipped via `gmail_message_id`  
8. Message may be marked read (best-effort)

On constrained hosting, acceptance is fast (HTTP 202) and AI continues in the background.

## 3.3 Multi-Dimensional Classification

The classification node labels each email across:

| Dimension | Example values |
|-----------|----------------|
| Function | Sales, Hiring, Legal, Support, Ops, Marketing, Admin |
| Intent | Inquiry, Follow-up, Objection, Scheduling, Application, FAQ, Complaint |
| Urgency | Immediate, Soon, Can wait |
| Impact | Revenue, Hiring-critical, Brand-sensitive, Low |
| Confidence | Clear, Ambiguous, Missing information |

This turns unstructured mail into operational metadata.

## 3.4 Priority Scoring and Unified Queue

Classification signals are converted into a **priority score (0–100)**.  
Emails from all companies appear in one **Priority Queue**, sorted so urgent cross-tenant work is visible in a single screen.

## 3.5 Executive Summary and Action Recommendation

- **Summarizer:** produces a short meaning-focused summary (not a quote dump)  
- **Action recommender:** suggests next step, e.g. reply with template, ask for missing info, schedule meeting, escalate, hold/ignore  

## 3.6 Brand-Aware Draft Generation

When a reply-worthy action is selected, the draft generator:

- Loads company brand context from Google Drive (voice, policies, templates, knowledge)  
- Generates subject + body suited to function/intent/action  
- Stores a **pending draft** linked to the email/company  

## 3.7 Human Review, Send, and Logging

1. Admin opens **Drafts** / Priority Queue  
2. Reviews and optionally edits  
3. Approves or rejects  
4. n8n **Send Approved Drafts** sends via Gmail  
5. Status/logging/CRM updates occur as configured  

**No send without an approval path.**

## 3.8 Why This Counts as Multi-Agent / Agentic Automation

Although implemented as LangGraph nodes, the pipeline is agentic in practice:

- Specialized steps with distinct goals (classify vs score vs draft)  
- Tool/data use (tenant DB, Drive brand docs, Gmail via automation)  
- Stateful progression from raw mail to actionable draft  
- External actuation only after human gate  

This is **orchestrated multi-step AI**, not a single prompt.

---

# 4 Flow 2: Outbound B2B / B2C Drafting

## 4.1 Module Overview

Flow 2 covers cases where the company initiates outreach (not waiting for an inbound reply), especially CRM follow-ups.

Triggers:

- Manual: admin clicks **Send email** on a lead in the UI  
- Scheduled: n8n finds leads due for follow-up  

Pipeline idea: intent → recipient CRM context → template/brand → draft → human approve → send.

## 4.2 B2B Outbound (LEADS)

- Source: Google Sheets **LEADS** workbook/sheet  
- Typical use: institutions, demos, proposals, relationship follow-ups  
- Dashboard page: **B2B Outbound**

## 4.3 B2C Outreach (B2C_FUNNEL)

- Source: **B2C_FUNNEL** sheet  
- Typical use: social/campaign commenter follow-ups and consumer sequences  
- Dashboard page: **B2C Outreach**

## 4.4 CRM Integration via Google Sheets

CRM templates (repository `CRM_TEMPLATES/`) define expected columns for leads, funnel stages, activities, and tasks.  
The backend reads sheet data for recipient context and can update CRM fields after successful sends (via configured workflows/APIs).

If a lead replies, the reply re-enters **Flow 1** with thread context when available.

---

# 5 Admin Dashboard and Multi-Tenant Management

## 5.1 Dashboard Modules

| Module | Purpose |
|--------|---------|
| Dashboard | High-level operational stats |
| Priority Queue | Cross-company urgent inbound work |
| Drafts | Review / edit / approve / reject |
| Emails | Processed email history |
| B2B Outbound | Business lead outreach |
| B2C Outreach | Consumer/campaign outreach |
| Companies | Tenant lifecycle + OAuth |

## 5.2 Company Onboarding and OAuth

1. Admin adds company (name + email)  
2. Connects Gmail & Drive via Google OAuth  
3. Tokens stored encrypted on the company record  
4. Company Drive holds CRM workbook + brand documents  
5. Company can later be deleted with cascade of related platform rows  

On Render deployments, OAuth callback is handled by the **backend** (so public n8n is not required for connect).

## 5.3 Draft Approval Workspace

The Drafts module is the safety and quality gate:

- Pending AI drafts are editable  
- Approval authorizes sending workflows  
- Rejection prevents send  

This operationalizes **human-in-the-loop AI**.

---

# 6 n8n Automation Layer

## 6.1 Role of n8n in the System

n8n is the **hands and scheduler** of the platform:

- Backend = intelligence + APIs + persistence  
- Dashboard = human control  
- n8n = timed Gmail polling, sending, and follow-up triggers  

This split keeps AI logic testable in the backend while operations remain visible as workflows.

## 6.2 Key Workflows

| Workflow | Purpose |
|----------|---------|
| Email Ingestion | Poll connected inboxes → process API |
| Send Approved Drafts | Send approved drafts through Gmail |
| B2B Follow-Up Drafts | Create drafts for B2B leads due |
| B2C Follow-Up Drafts | Create drafts for B2C leads due |
| Company OAuth Connection | Optional/local legacy helper |

## 6.3 Known Limitations

- Local Docker n8n requires the machine to stay on for schedules  
- Free hosted backends may cold-start and return temporary 502s  
- Gmail API rate limits require sequential batching/retries  
- Workflow JSON on disk must be re-imported to update a running n8n instance  

---

# 7 Results and Evaluation

## 7.1 Feature Completion Summary

| Feature | Status |
|---------|--------|
| Multi-company tenancy | Completed |
| Gmail OAuth connect | Completed |
| Flow 1 inbound pipeline | Completed |
| Priority Queue + Drafts UI | Completed |
| Flow 2 B2B/B2C drafts | Completed |
| n8n ingestion/send workflows | Completed |
| Human approval before send | Completed |
| Cloud deploy (frontend/backend) | Completed |
| Hiring Flows 3–4 | Not implemented (blueprint only) |

## 7.2 Before vs After

| Before | After (with platform) |
|--------|------------------------|
| Separate inboxes, no shared priority | Unified Priority Queue across companies |
| Manual reading/triage | AI classification + scoring |
| Ad-hoc reply writing | Brand-aware editable drafts |
| Easy-to-miss CRM follow-ups | B2B/B2C outbound draft flows |
| Risky auto-send or slow manual send | Human approve → automated send |

## 7.3 Challenges Faced and Resolved

| Challenge | Resolution |
|-----------|------------|
| Long AI calls timing out on free hosting | Fast accept (202) + background Flow 1 |
| Parallel AI jobs destabilizing free tier | Serialize processing; limit emails per run |
| Gmail concurrent request errors | Batch size 1, retries, continue-on-fail |
| OAuth without public n8n | Backend OAuth callback |
| Environment/setup friction | Documented `.venv`, run order, Render notes |

## 7.4 Honest Limitations Summary

- Hiring automation not built yet  
- Draft quality depends on OpenAI + quality of brand docs  
- n8n availability depends on hosting choice (local vs always-on)  
- Free-tier cloud sleep/cold starts affect reliability  
- Evaluation is primarily functional/end-to-end, not large-scale A/B metrics  

---

# 8 Conclusion and Future Scope

## 8.1 Conclusion

This summer internship work on the **S Combinator Central Agent Platform** delivered a practical multi-tenant AI email operations system for customer acquisition. The platform:

- Connects multiple company Gmail accounts  
- Runs a structured LangGraph pipeline for inbound understanding and drafting  
- Supports outbound B2B/B2C drafts from CRM  
- Keeps humans in control through an approval workspace  
- Uses n8n for reliable operational scheduling around Gmail  

The main academic and engineering takeaway is that production GenAI value comes from **system design**—tenancy, integrations, orchestration, and safety—not from a single prompt.

## 8.2 Future Scope

1. Implement **Hiring Flows 3 and 4** from the blueprint  
2. Deploy **always-on n8n** (or equivalent) for production schedules  
3. Add draft-quality evaluation and analytics (time-to-reply, conversion)  
4. Role-based access for company managers (beyond global admin)  
5. Notifications (Slack/Teams) for high-priority emails  
6. Richer CRM write-backs and multi-step sequences  
7. Multilingual drafting and deeper attachment understanding  

---

# References

1. FastAPI Documentation — https://fastapi.tiangolo.com/  
2. LangGraph Documentation — https://langchain-ai.github.io/langgraph/  
3. LangChain Documentation — https://python.langchain.com/  
4. OpenAI Platform Docs — https://platform.openai.com/docs  
5. React Documentation — https://react.dev/  
6. PostgreSQL Documentation — https://www.postgresql.org/docs/  
7. n8n Documentation — https://docs.n8n.io/  
8. Gmail API — https://developers.google.com/gmail/api  
9. Google Drive API — https://developers.google.com/drive  
10. Google Sheets API — https://developers.google.com/sheets  
11. Render Documentation — https://render.com/docs  
12. Project blueprint: *S Combinator — Central Agent Platform (Customer Acquisition and Hiring)* (internal)  
13. Project README and `PROJECT_FLOW.mmd` (repository)  

---

*End of Internship Report Source Document*
