# Test Emails for Flow 1 Brand Context Integration

Use these emails to test different scenarios and verify brand context is working correctly.

---

## Test Email 1: Pricing Inquiry (Tests Pricing Policy)

**Subject:** Interested in your services - pricing information needed

**Body:**
```
Hi there,

I came across your company and I'm interested in learning more about your services. 
Could you please provide me with detailed pricing information? 

We're a growing startup and looking for a solution that fits our budget. 
What packages do you offer and what's included in each tier?

Also, do you offer any discounts for annual subscriptions?

Looking forward to hearing from you.

Best regards,
Sarah Johnson
sarah.johnson@example.com
```

**Expected Results:**
- ✅ Classification: Sales, Inquiry, Revenue impact
- ✅ Priority Score: 75-90
- ✅ Action: Reply with template (should route to call, NOT discuss pricing)
- ✅ Template Matched: `responses/pricing_inquiry.md`
- ✅ Draft should: Route to call, NOT mention pricing tiers/packages
- ✅ Draft should use: "Best," not "Best regards"
- ✅ Draft should be: Short, direct, friendly

---

## Test Email 2: Product Demo Request (Tests Sales Flow)

**Subject:** Request for product demonstration

**Body:**
```
Hello,

I've been researching solutions for our team and your platform looks promising. 
I'd like to schedule a demo to see how it works in practice.

We're a team of about 20 people and would need to understand:
- How the onboarding process works
- Integration capabilities with our existing tools
- Training and support options

Please let me know your availability for next week.

Thanks,
Michael Chen
michael.chen@techstartup.com
```

**Expected Results:**
- ✅ Classification: Sales, Scheduling, Revenue impact
- ✅ Priority Score: 80-90
- ✅ Action: Schedule meeting
- ✅ Draft should: Suggest specific times, be helpful and friendly

---

## Test Email 3: Support/Technical Question (Tests Support Flow)

**Subject:** Question about integration with our systems

**Body:**
```
Hi Team,

We're currently evaluating your platform and have a few technical questions:

1. Does your API support webhook integrations?
2. What authentication methods do you support?
3. Is there a sandbox environment for testing?

We need to integrate this with our CRM system (Salesforce) and want to make sure 
everything will work smoothly before we commit.

Appreciate your help!

Regards,
David Rodriguez
david.rodriguez@company.com
```

**Expected Results:**
- ✅ Classification: Support, Inquiry, Low impact
- ✅ Priority Score: 30-50
- ✅ Action: Reply with template
- ✅ Draft should: Answer questions, be helpful, technical but clear

---

## Test Email 4: Job Application (Tests Hiring Flow)

**Subject:** Application for Full-Stack Engineer Position

**Body:**
```
Hello,

I'm writing to apply for the Full-Stack Engineer position I saw on your website. 
I have 5 years of experience building scalable web applications using Python, 
JavaScript, and React.

I've attached my resume for your review. I'm particularly interested in your 
AI-powered customer support platform and would love to contribute to your team.

I'm available for an interview at your convenience.

Best regards,
Priya Sharma
priya.sharma@email.com
```

**Expected Results:**
- ✅ Classification: Hiring, Application, Hiring impact
- ✅ Priority Score: 70-85
- ✅ Action: Review resume
- ✅ Draft should: Acknowledge application, set expectations, mention timeline

---

## Test Email 5: General Inquiry (Tests General Flow)

**Subject:** Quick question about your services

**Body:**
```
Hi,

I saw your website and wanted to reach out. Can you tell me more about what you do 
and who your typical clients are?

We're always looking for partners that can help us scale our operations.

Thanks,
Emily Watson
emily@newbusiness.io
```

**Expected Results:**
- ✅ Classification: Sales, Inquiry, Low impact
- ✅ Priority Score: 40-60
- ✅ Action: Reply with template
- ✅ Draft should: Be informative, mention company value prop, suggest next steps

---

## Test Email 6: Urgent Support Issue (Tests Urgency & Escalation)

**Subject:** URGENT - System Integration Issue

**Body:**
```
Hi,

We're experiencing a critical issue with the integration. Our customers can't 
access their accounts through the API. This is affecting our production system 
right now.

We need immediate assistance to resolve this. Please escalate this to your 
technical team ASAP.

This is urgent - our business is impacted.

Thanks,
Raj Patel
raj.patel@urgentcompany.com
```

**Expected Results:**
- ✅ Classification: Support, Complaint, Immediate urgency, Brand impact
- ✅ Priority Score: 90-100
- ✅ Action: Escalate to human
- ✅ Draft should: Acknowledge urgency, provide immediate response, escalate

---

## How to Test

### Option 1: Via API Endpoint

```bash
curl -X POST "http://localhost:8000/api/flow1/process-email" \
  -H "Content-Type: application/json" \
  -H "Authorization: Bearer YOUR_TOKEN" \
  -d '{
    "company_id": "74799dff-c12e-4d52-ab1e-c009363574ef",
    "email_data": {
      "subject": "Interested in your services - pricing information needed",
      "body": "Hi there,\n\nI came across your company...",
      "from": "sarah.johnson@example.com",
      "to": "hello@resolvely.io",
      "thread_id": null,
      "gmail_message_id": null
    }
  }'
```

### Option 2: Via Test Script

Modify `test_flow1_with_brand_context.py` to use different email data, then run:

```bash
cd backend
python test_flow1_with_brand_context.py 74799dff-c12e-4d52-ab1e-c009363574ef
```

### Option 3: Via n8n Workflow

Trigger your n8n workflow with any of these test emails.

---

## What to Check After Testing

1. **Classification:**
   - ✅ Function, Intent, Urgency, Impact, Confidence are correct
   - ✅ Company name from brand context is used

2. **Priority Score:**
   - ✅ Score is reasonable (0-100)
   - ✅ SLA rules from brand context are considered

3. **Executive Summary:**
   - ✅ Explains business meaning, not just content
   - ✅ Company context is included

4. **Recommended Action:**
   - ✅ Follows company policies (especially pricing policy)
   - ✅ Appropriate for the email type

5. **Draft:**
   - ✅ Uses brand voice (no "Best regards", uses contractions)
   - ✅ Follows company policies (pricing → route to call)
   - ✅ Uses matched template when available
   - ✅ Company-specific information included
   - ✅ Short, direct, friendly tone

6. **Logs:**
   - ✅ "Brand context loaded from cache" (after first request)
   - ✅ "Using matched template: ..." (when template matches)
   - ✅ All nodes processed successfully

---

## Recommended Test Sequence

1. **Start with Test Email 1 (Pricing)** - Most important, tests pricing policy
2. **Then Test Email 2 (Demo)** - Tests scheduling flow
3. **Then Test Email 4 (Hiring)** - Tests hiring flow
4. **Then Test Email 6 (Urgent)** - Tests escalation

This will verify all major flows are working with brand context!

