**Outbound Email Use Cases** 

Implementation Guide for Development Team 

**Overview** 

This agent platform automates customer acquisition email workflows across three main channels: **B2B Sales**, **B2C Outreach**, and **Marketing Automation**. All workflows include human-in-the-loop approval for drafts before sending. 

**1\. B2B Sales Emails (Post Lead Generation)** 

These are relationship-driven, high-touch emails for qualified leads moving through a sales pipeline.

| Email Type  | Trigger  | Purpose  | Approval |
| :---- | ----- | ----- | :---- |
| Meeting Follow-up  | Calendar event  completed | Recap discussion, confirm next steps  | Yes |
| Product Info Send  | Rep request or lead asks  | Deliver brochures, one-pagers, case studies | Yes |
| Demo Scheduling  | Lead qualified for demo  | Propose times, set expectations  | Yes |
| Post-Demo Follow-up  | Demo completed  | Address questions, share  recording/slides | Yes |
| Nurture/Check-in  | X days since last contact  | Keep relationship warm, gauge interest  | Yes |
| Proposal/Agreement  | Deal stage \=  "Negotiation" | Send SOWs, contracts, pricing  | Yes |
| FAQ/Objection  Handling | Common objection  detected | Proactively address concerns  | Yes |
| Onboarding Handoff  | Deal closed-won  | Introduce CS team, share SOPs  | Yes |

**2\. B2C Outreach Emails (Lead Generation & Cold Outreach)** These are volume-driven, conversion-focused emails for acquiring new customers. 

**2a. Lead Identification & Cold Outreach** 

| Email Type  | Trigger  | Purpose  | Channel |
| :---- | :---- | ----- | ----- |
| Initial Cold Outreach  | Lead identified via  social/intent data | Introduce product, spark interest  | Email \+ WhatsApp |
| Follow-up \#1  | No response after 3 days  | Gentle reminder with value prop  | Email |
| Follow-up \#2  | No response after 7 days  | Different angle or offer  | Email \+ WhatsApp |
| Break-up Email  | No response after 14 days  | Final attempt, create urgency  | Email |

**2b. Engaged Lead Nurturing**

| Email Type  | Trigger  | Purpose |
| :---- | :---- | :---- |
| Product Demo/How-to  | Lead expressed interest  | Share video walkthroughs, tutorials |
| Feature Highlights  | Lead viewed specific pages  | Deep-dive on relevant features |
| Pricing/Access Info  | Lead requested pricing  | Send plans, policies, access details |
| Testimonials/Reviews  | Lead in consideration phase  | Build trust with social proof |

**3\. Marketing Automation (Lifecycle Emails)** 

These are behavior-triggered, automated emails for both prospects and existing users. 

**3a. Newsletter Campaigns** 

| Campaign Type  | Audience  | Frequency  | Content |
| :---- | :---- | :---- | :---- |
| Product Updates  | All subscribers  | Bi-weekly/Monthly  | New features, improvements |
| Feature Launch  | Relevant segments  | As released  | Deep-dive on new capability |
| Industry Insights  | B2B subscribers  | Monthly  | Thought leadership, trends |
| Tips & Best Practices  | Active users  | Weekly  | How to get more value |

**3b. Product Activation & Retention**

| Email Type  | Trigger Condition  | Goal |
| ----- | :---- | :---- |
| Welcome  | Account created  | Set expectations, first action |
| Setup Incomplete  | Created account, no setup after 24h  | Complete onboarding |
| First Value  | Setup complete, no key action taken  | Drive to "aha moment" |
| Dormant User  | No login for 7+ days  | Re-engage |
| Win-back  | No login for 30+ days  | Prevent churn |
| New Feature Announcement  | Feature released \+ user is relevant  | Drive adoption |
| Usage Milestone  | User hits milestone (10 tasks, etc.)  | Celebrate, encourage upgrade |

**4\. Cross-Cutting Concerns (Critical for Implementation)** 

**4a. Compliance & Legal** 

• **Unsubscribe handling** — one-click unsubscribe, preference center 

• **GDPR/CAN-SPAM** — consent tracking, regional compliance 

• **Data retention** — how long to keep contact data 

**4b. Agent Workflow Configuration** 

• **Human approval gate** — all drafts require approval before send 

• **Escalation rules** — when to involve a human (angry reply, legal mention) 

• **Personalization depth** — what data the agent can use 

• **Tone calibration** — formal vs. casual per segment 

**4c. Required Integrations** 

| System  | Purpose |
| :---- | :---- |
| CRM  | Lead data, deal stages, activity history |
| Calendar  | Meeting triggers, scheduling |
| Social Media APIs  | Lead identification, intent signals |
| WhatsApp Business API  | Multi-channel outreach |
| Email Provider  | Sending, deliverability, tracking |
| Analytics  | Open rates, click rates, conversions |

**4d. Key Metrics to Track** 

• Open rate, click rate, reply rate 

• Conversion rate per sequence 

• Time-to-response 

• Unsubscribe rate  
• Human approval turnaround time  
**5\. Suggested Email Sequence Templates** 

Pre-built templates for your development team to implement: 

**B2B Outbound Sequence** 

| Day  | Action |
| :---- | :---- |
| Day 0  | Initial outreach |
| Day 3  | Follow-up \#1 (new angle) |
| Day 7  | Follow-up \#2 (social proof) |
| Day 14  | Break-up email |

**Post-Demo Sequence** 

| Day  | Action |
| :---- | :---- |
| Day 0  | Thank you \+ recap |
| Day 2  | Address common objections |
| Day 5  | Case study relevant to their use case |
| Day 10  | Check-in / decision timeline |

**Product Activation Sequence**

| Timing  | Action |
| :---- | :---- |
| Hour 0  | Welcome email |
| Hour 24  | Setup reminder (if incomplete) |
| Day 3  | First value prompt |
| Day 7  | Tips email |
| Day 14  | Dormant re-engagement |

