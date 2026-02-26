
# Outbound Email Use Cases
## Implementation Guide for Development Team

---

## Overview
This agent platform automates **customer acquisition email workflows** across three main channels:

- **B2B Sales**
- **B2C Outreach**
- **Marketing Automation**

> 🔐 All workflows include **human-in-the-loop approval** before emails are sent.

---

## 1. B2B Sales Emails (Post Lead Generation)

High-touch, relationship-driven emails for qualified leads in the sales pipeline.

| Email Type | Trigger | Purpose | Approval |
|---------|--------|--------|---------|
| Meeting Follow-up | Calendar event completed | Recap discussion, confirm next steps | ✅ Yes |
| Product Info Send | Rep request or lead asks | Share brochures, one-pagers, case studies | ✅ Yes |
| Demo Scheduling | Lead qualified for demo | Propose times, set expectations | ✅ Yes |
| Post-Demo Follow-up | Demo completed | Address questions, share recordings/slides | ✅ Yes |
| Nurture / Check-in | X days since last contact | Keep relationship warm | ✅ Yes |
| Proposal / Agreement | Deal stage = Negotiation | Send SOWs, contracts, pricing | ✅ Yes |
| FAQ / Objection Handling | Objection detected | Proactively resolve concerns | ✅ Yes |
| Onboarding Handoff | Deal closed-won | Introduce CS team, share SOPs | ✅ Yes |

---

## 2. B2C Outreach Emails

Volume-driven, conversion-focused emails.

### 2a. Lead Identification & Cold Outreach

| Email Type | Trigger | Purpose | Channel |
|----------|--------|--------|--------|
| Initial Cold Outreach | Lead identified via intent/social data | Introduce product, spark interest | Email + WhatsApp |
| Follow-up #1 | No response after 3 days | Gentle reminder | Email |
| Follow-up #2 | No response after 7 days | New angle or offer | Email + WhatsApp |
| Break-up Email | No response after 14 days | Final attempt, urgency | Email |

### 2b. Engaged Lead Nurturing

| Email Type | Trigger | Purpose |
|----------|--------|--------|
| Product Demo / How-to | Lead showed interest | Share tutorials, walkthroughs |
| Feature Highlights | Page views | Deep-dive on features |
| Pricing / Access Info | Pricing requested | Send plans & policies |
| Testimonials / Reviews | Consideration phase | Build trust |

---

## 3. Marketing Automation (Lifecycle Emails)

Behavior-triggered automation for prospects and users.

### 3a. Newsletter Campaigns

| Campaign Type | Audience | Frequency | Content |
|-------------|---------|----------|--------|
| Product Updates | All subscribers | Bi-weekly / Monthly | New features |
| Feature Launch | Relevant segments | As released | Feature deep-dive |
| Industry Insights | B2B subscribers | Monthly | Thought leadership |
| Tips & Best Practices | Active users | Weekly | Product value tips |

### 3b. Product Activation & Retention

| Email Type | Trigger Condition | Goal |
|----------|-----------------|-----|
| Welcome | Account created | Set expectations |
| Setup Incomplete | No setup after 24h | Complete onboarding |
| First Value | Setup done, no key action | Drive aha moment |
| Dormant User | No login 7+ days | Re-engage |
| Win-back | No login 30+ days | Prevent churn |
| Feature Announcement | Feature released | Drive adoption |
| Usage Milestone | Milestone reached | Celebrate & upsell |

---

## 4. Cross-Cutting Concerns

### 4a. Compliance & Legal
- One-click unsubscribe
- GDPR / CAN-SPAM compliance
- Data retention policies

### 4b. Agent Workflow Configuration
- Human approval gate
- Escalation rules
- Personalization depth
- Tone calibration

### 4c. Required Integrations

| System | Purpose |
|------|--------|
| CRM | Lead & deal data |
| Calendar | Scheduling triggers |
| Social APIs | Lead intent |
| WhatsApp Business API | Multi-channel outreach |
| Email Provider | Sending & tracking |
| Analytics | Performance metrics |

### 4d. Key Metrics
- Open, click & reply rates
- Conversion per sequence
- Time-to-response
- Unsubscribe rate
- Human approval turnaround time

---

## 5. Suggested Email Sequences

### B2B Outbound Sequence

| Day | Action |
|----|-------|
| Day 0 | Initial outreach |
| Day 3 | Follow-up #1 |
| Day 7 | Follow-up #2 |
| Day 14 | Break-up email |

### Post-Demo Sequence

| Day | Action |
|----|-------|
| Day 0 | Thank you + recap |
| Day 2 | Objection handling |
| Day 5 | Relevant case study |
| Day 10 | Decision check-in |

### Product Activation Sequence

| Timing | Action |
|------|-------|
| Hour 0 | Welcome email |
| Hour 24 | Setup reminder |
| Day 3 | First value prompt |
| Day 7 | Tips email |
| Day 14 | Dormant re-engagement |

---

✨ *Markdown-ready, cleanly structured, and developer-friendly.*
