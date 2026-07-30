 **S Combinator — Central Agent Platform (v1)**

Focus: Clear, step-by-step operational flows  
Scope: Multi-company (parent  spin-offs) | Customer Acquisition  Hiring  
Design Principle:  Convert raw inputs → structured understanding → prioritized decisions → editable drafts → logged outcomes

It focuses only on what happens, in what order, so you can clearly map the system in your head.

 **PART A — CUSTOMER ACQUISITION**

 **FLOW 1: INBOUND EMAIL → RESPONSE**  
(Someone emails a company inbox and expects a reply)

 Step 1: Email Ingestion & Company Identification  
 Email is received in a Gmail inbox  
 Inbox is mapped to a specific company (tenant)  
 Thread context is identified (new / existing)

Output  
 Email tagged with companyid  
 Thread context established

 Step 2: Reading & Multi-Dimensional Understanding  
AI reads the email and classifies it across multiple dimensions:

 Function



  
  Sales / Hiring / Legal / Support / Ops / Marketing / Admin  
 Intent  
  Inquiry / Follow-up / Objection / Scheduling / Application / FAQ / Complaint  
 Urgency  
  Immediate / Soon / Can wait  
 Impact  
  Revenue-impacting / Hiring-critical / Brand-sensitive / Low impact  
 Confidence  
  Clear request / Ambiguous / Missing information

Output  
 Structured classification metadata

 Step 3: Priority Scoring  
 Classification signals are converted into a numeric priority score  
 Company context is applied (stage, importance, SLAs)

Output  
 Priority score (0–100)  
 Placement in a unified, cross-company priority queue

 Step 4: Zero-Context Executive Summary  
 AI generates a 1–2 line summary  
 Summary explains what the email means, not what it says  
 No quoting, no fluff, no dependency on original email

Output  
 Executive-ready summary for quick understanding

 Step 5: Action Recommendation Layer  
AI suggests what should be done next:

 Reply with a specific template  
 Ask for missing information  
 Schedule a meeting  
 Hold / Ignore  
 Escalate to human

Output  
 Recommended next action

 Step 6: Drafting Layer (Editable)  
 Based on selected action  
 Loads company-specific:  
   Templates  
   Brand tone  
   Approved FAQs / pricing / references  
 Generates a draft reply

Output  
 Editable draft email  
 Subject line suggestions

 Step 7: Review, Send & Log  
 Human reviews and edits the draft  
 Email is sent  
 Conversation state and metadata are logged

Output  
 Sent response  
 Updated thread state  
 Audit record

 **FLOW 2: OUTBOUND EMAIL → SEND**  
(You want to send an email without waiting for a reply)

Examples:  
 New lead outreach  
 Marketing engagement  
 Sending agreements  
 Partner introductions

 Step 1: Intent Definition  
 User or system defines:  
   Why the email is being sent  
   Which company it belongs to

Output  
 Outbound intent  company context

 Step 2: Recipient Context Gathering  
 Collect recipient details:  
   Name, company, role  
   Lead stage (new / warm / existing)  
 Optional enrichment (from sheets or CRM)

Output  
 Enriched recipient profile

 Step 3: Template Selection  
 AI selects the best company-specific template  
 Based on:  
   Intent  
   Recipient type  
   Relationship stage

Output  
 Selected template  
 Required variables identified

 Step 4: Draft Generation  
 Variables auto-filled  
 Brand tone applied  
 CTA adjusted (reply / call / review doc)

Output  
 Draft outbound email

 Step 5: Review & Scheduling  
 Human reviews and edits  
 Choose:  
   Send immediately  
   Schedule for later  
   Add to a follow-up sequence

Output  
 Scheduled or sent email

 Step 6: Tracking & Feedback Loop  
 Replies (if any) return into Inbound Email → Response flow  
 Engagement status updated

Output  
 Closed-loop communication tracking

 **PART B — HIRING & TALENT MANAGEMENT**

 **FLOW 3: PRE-HIRING**  
(Applications → Screening → Shortlisting)

 Step 1: Resume / Application Ingestion  
 Resume received via email or upload  
 Mapped to:  
   Company  
   Role (or AI suggests role)

Output  
 Candidate record created

 Step 2: Resume Understanding & Signal Extraction  
AI extracts only role-relevant information:

 Skills  
 Evidence of execution  
 Experience depth  
 Red flags

Output  
 Structured candidate signals

 Step 3: Role-Aware Evaluation  
 Compare candidate signals against role blueprint:  
   Must-haves  
   Nice-to-haves  
   Disqualifiers

Output  
 Fit score

 Step 4: Zero-Context Candidate Summary  
AI produces a concise summary:

 2–3 line overview  
 Strengths  
 Gaps

Output  
 One-screen candidate snapshot

 Step 5: Verdict & Shortlisting  
AI suggests:  
 Strong Yes  
 Maybe  
 Reject  
 Or “better fit for another company”

Output  
 Updated hiring pipeline state

 **FLOW 4: POST-HIRING**  
(Interview → Decision → Communication)

 Step 1: Interview Kit Preparation  
 Generate:  
   Candidate-specific interview questions  
   Practical task ideas  
   Evaluation focus areas

Output  
 Interview kit for interviewers

 Step 2: Interview Scheduling  
 Send scheduling email using company calendar  
 Send reminders automatically

Output  
 Interview scheduled and logged

 Step 3: Decision Recording  
 Capture interview feedback  
 Record final decision:  
   Offer  
   Reject  
   Hold

Output  
 Decision state saved

 Step 4: Decision Communication  
 AI drafts:  
   Offer email  
   Rejection email  
 Company tone preserved  
 Human approves and sends

Output  
 Candidate informed  
 Employer brand consistency

 Step 5: Hiring Visibility & Digest  
 Aggregate hiring status across companies  
 Highlight:  
   Pending decisions  
   Bottlenecks  
   Strong candidates

Output  
 Clear hiring overview for founder

 **FINAL CONSOLIDATED VIEW**

You are building four core operational pipelines:

1 Inbound Email → Understand → Decide → Respond  
2 Outbound Intent → Draft → Send → Track  
3 Resume → Signal → Verdict  
4 Interview → Decision → Communicate

Each pipeline is:  
 Company-aware  
 Priority-driven  
 Summary-first  
 Human-controlled  
 Fully logged

This document represents the behavioral blueprint of the agent platform.