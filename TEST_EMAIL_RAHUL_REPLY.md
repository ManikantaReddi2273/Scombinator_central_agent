# Test Email: Rahul's Reply to Manish's Demo Scheduling Email

## Context
This is a **follow-up email** in a thread. Manish already sent a demo scheduling email with time slots. Now Rahul is replying.

---

## Test Email Option 1: Confirming a Time Slot

**Subject:** Re: Request for product demonstration

**Body:**
```
Hi Manish,

Thanks for the quick response! Tuesday at 3 PM IST works perfectly for me.

Looking forward to the demo and learning more about how Resolvely can help our team.

See you then!

Best regards,
Rahul
TCS
```

**Expected Results:**
- ✅ Classification: Sales, Follow-up, Revenue impact
- ✅ Thread Count: 1 (this is the 2nd email in thread)
- ✅ Action: Reply with template
- ✅ Draft should: Acknowledge the confirmation, confirm meeting details, be brief

---

## Test Email Option 2: Suggesting Alternative Time

**Subject:** Re: Request for product demonstration

**Body:**
```
Hi Manish,

Thanks for the time slots. Unfortunately, those times don't work for me next week.

Would it be possible to schedule the demo for Friday afternoon, around 2-3 PM IST? Or early next week?

Let me know what works for you.

Thanks,
Rahul
TCS
```

**Expected Results:**
- ✅ Classification: Sales, Follow-up, Revenue impact
- ✅ Thread Count: 1
- ✅ Action: Schedule meeting (rescheduling)
- ✅ Draft should: Acknowledge their request, suggest new times, be flexible

---

## Test Email Option 3: Asking Follow-up Questions Before Demo

**Subject:** Re: Request for product demonstration

**Body:**
```
Hi Manish,

Thanks for the availability. Before we schedule the demo, I have a few quick questions:

1. Does Resolvely integrate with ServiceNow? We're currently using that for our IT service management.
2. What's the typical implementation timeline for a team of 20 people?
3. Do you offer a trial period before we commit?

Once I have these answers, we can schedule the demo.

Thanks,
Rahul
TCS
```

**Expected Results:**
- ✅ Classification: Sales, Inquiry, Revenue impact
- ✅ Thread Count: 1
- ✅ Action: Reply with template (answer questions)
- ✅ Draft should: Answer questions directly, then suggest scheduling demo

---

## Test Email Option 4: Confirming with Additional Context

**Subject:** Re: Request for product demonstration

**Body:**
```
Hi Manish,

Tuesday at 3 PM IST works great for me. I've added it to my calendar.

Just to give you some context before the demo:
- We're using Freshdesk currently
- Our e-commerce platform is Shopify
- We handle about 800-1000 support tickets per month

Looking forward to seeing how Resolvely can help us automate some of these.

See you Tuesday!

Best,
Rahul
TCS
```

**Expected Results:**
- ✅ Classification: Sales, Follow-up, Revenue impact
- ✅ Thread Count: 1
- ✅ Action: Reply with template
- ✅ Draft should: Acknowledge confirmation, thank for context, confirm meeting

---

## Recommended Test Email (Most Realistic)

**Subject:** Re: Request for product demonstration

**Body:**
```
Hi Manish,

Thanks for the quick response! Tuesday at 3 PM IST works perfectly for me.

I've added it to my calendar. Looking forward to the demo and learning more about how Resolvely can help our team of 20 people.

See you then!

Best regards,
Rahul
TCS
```

**Why This is Good for Testing:**
- ✅ Tests thread history handling (system should see previous email)
- ✅ Tests follow-up classification
- ✅ Tests confirmation response
- ✅ Realistic and natural
- ✅ Short and direct

---

## What to Verify After Processing

1. **Thread History:**
   - ✅ System should see Manish's previous email
   - ✅ Draft should reference the scheduled meeting
   - ✅ Should acknowledge the confirmation

2. **Classification:**
   - ✅ Function: Sales
   - ✅ Intent: Follow-up (not Inquiry)
   - ✅ Thread Count: 1

3. **Draft Quality:**
   - ✅ Acknowledges the confirmation
   - ✅ Confirms meeting details (Tuesday 3 PM IST)
   - ✅ Brief and friendly
   - ✅ Uses brand voice ("Best," not "Best regards")

4. **Logs:**
   - ✅ "CONVERSATION HISTORY" should be in prompt
   - ✅ Thread context should be included

---

## How to Test

### Option 1: Via API (with thread history)

```json
{
  "company_id": "74799dff-c12e-4d52-ab1e-c009363574ef",
  "email_data": {
    "subject": "Re: Request for product demonstration",
    "body": "Hi Manish,\n\nThanks for the quick response! Tuesday at 3 PM IST works perfectly for me.\n\nI've added it to my calendar. Looking forward to the demo.\n\nBest regards,\nRahul\nTCS",
    "from": "rahul@tcs.com",
    "to": "arjunreddi2273@gmail.com",
    "thread_id": "thread_123",
    "gmail_message_id": "msg_456",
    "thread_history": [
      {
        "subject": "Request for product demonstration",
        "from_email": "rahul@tcs.com",
        "body": "Hello,\n\nI've been researching solutions...",
        "sent_at": "2026-02-17T14:00:00Z"
      },
      {
        "subject": "Re: Request for product demonstration",
        "from_email": "arjunreddi2273@gmail.com",
        "body": "Hi Rahul,\n\nThanks for reaching out!...",
        "sent_at": "2026-02-17T14:38:00Z"
      }
    ],
    "thread_count": 1
  }
}
```

### Option 2: Via n8n Workflow

Trigger your n8n workflow with the email above, including thread history.

---

## Expected Draft Response from Resolvely

After processing Rahul's confirmation email, the system should generate something like:

```
Hi Rahul,

Great! I've confirmed Tuesday at 3 PM IST on my calendar as well.

I'll send you a calendar invite with the meeting link shortly. The demo will be about 30 minutes, and I'll show you how Resolvely works with your setup.

Looking forward to showing you how we can help your team!

Best,
Manish
```

**Key Points:**
- ✅ Acknowledges the confirmation
- ✅ Confirms the time
- ✅ Mentions next steps (calendar invite)
- ✅ Brief and friendly
- ✅ Uses "Best," not "Best regards"

