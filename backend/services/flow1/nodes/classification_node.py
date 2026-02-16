"""
Classification Node - Step 2 of Flow 1
Multi-dimensional email classification using OpenAI
"""
from typing import Dict
from services.flow1.state import Flow1State
from services.openai_client import openai_client
import logging

logger = logging.getLogger(__name__)


async def classification_node(state: Flow1State) -> Dict:
    """
    Step 2: Multi-Dimensional Understanding
    
    Classifies email across multiple dimensions:
    - Function: Sales/Hiring/Legal/Support/Ops/Marketing/Admin
    - Intent: Inquiry/Follow-up/Objection/Scheduling/Application/FAQ/Complaint
    - Urgency: Immediate/Soon/Can wait
    - Impact: Revenue/Hiring/Brand/Low
    - Confidence: Clear/Ambiguous/Missing info
    
    Args:
        state: Flow1State with email_subject and email_body
        
    Returns:
        Dict with updated classification fields
    """
    subject = state.get("email_subject", "")
    body = state.get("email_body", "")
    thread_history = state.get("thread_history", [])  # Always a list
    thread_count = state.get("thread_count", 0)  # Always an int
    
    # Truncate body to 2000 chars to avoid token limits
    body_truncated = body[:2000] if len(body) > 2000 else body
    
    # Build thread context if available
    thread_context = ""
    if len(thread_history) > 0:
        thread_context = "\n\nCONVERSATION HISTORY (previous emails in this thread):\n"
        for i, prev_email in enumerate(thread_history, 1):
            prev_body = prev_email.get("body", "")[:300]  # Truncate to 300 chars for context
            thread_context += f"\n--- Previous Email {i} ---\n"
            thread_context += f"Subject: {prev_email.get('subject', 'N/A')}\n"
            thread_context += f"From: {prev_email.get('from_email', 'N/A')}\n"
            thread_context += f"Body: {prev_body}\n"
        
        thread_context += "\nNOTE: This appears to be a follow-up email. Consider the conversation context when classifying. If this continues a previous discussion, mark intent as 'Follow-up'."
    
    # Enhanced prompt with detailed examples and clear instructions
    prompt = f"""You are an expert business email classifier. Analyze this email CAREFULLY and classify it across 5 dimensions. Read the ENTIRE email, not just the subject.

EMAIL TO CLASSIFY:
Subject: {subject}
Body: {body_truncated}
{thread_context}

CRITICAL: Read the FULL email body to understand the actual purpose. Don't just look at keywords - understand the business context.

CLASSIFICATION DIMENSIONS:

1. FUNCTION (choose ONE - THIS IS CRITICAL):
   - Sales: Questions about products/services, pricing, purchasing, demos, sales opportunities, quotes, proposals
     * KEYWORDS: "pricing", "price", "cost", "quote", "purchase", "buy", "interested in", "demo", "trial", "enterprise", "subscription"
     * If email mentions pricing, cost, or purchasing → ALWAYS choose Sales, NOT Admin
   - Hiring: Job applications, resumes, recruitment inquiries, candidate communications, talent acquisition, interview requests
   - Support: Technical issues, bug reports, help requests, troubleshooting, account problems, feature questions
   - Legal: Contracts, agreements, compliance questions, legal matters, terms and conditions, liability, disputes
   - Ops: Operations, logistics, shipping, fulfillment, supply chain, delivery, inventory, order status
   - Marketing: Promotions, campaigns, partnerships, events, newsletters, content requests, PR inquiries
   - Admin: General administrative tasks, billing, account management, internal communications
     * ONLY use Admin if it's clearly NOT Sales, Hiring, Support, Legal, Ops, or Marketing
     * If email is about pricing/purchasing → Sales, NOT Admin
     * If email is about a job/application → Hiring, NOT Admin
     * Admin is the LAST resort, not the default

2. INTENT (choose ONE):
   - Inquiry: Initial question, information request, seeking details, asking "how", "what", "when", "where"
   - Follow-up: Following up on previous email/conversation, checking status, "did you see my email", "any update"
   - Objection: Concerns, hesitations, objections, pushback, "too expensive", "not interested", "we use competitor"
   - Scheduling: Requesting meetings, calls, appointments, calendar coordination, "can we schedule", "when are you available"
   - Application: Job application submission, resume attached, "I'm applying for", "interested in position"
   - FAQ: Frequently asked question, common query, standard information request, "how do I", "what is"
   - Complaint: Unhappy customer, dissatisfaction, issue escalation, "disappointed", "not working", "poor service"

3. URGENCY (choose ONE):
   - Immediate: Words like "urgent", "ASAP", "emergency", "critical", "deadline today/tomorrow", "need help now"
   - Soon: Time-sensitive but not emergency, "this week", "by Friday", "need response soon", "time-sensitive"
   - Can wait: Standard response time acceptable, no deadline mentioned, routine inquiry, "when you have time"

4. IMPACT (choose ONE):
   - Revenue: Direct sales impact, potential deals, pricing inquiries, enterprise customers, "interested in purchasing"
   - Hiring: Talent acquisition, critical role filling, senior positions, "we need to hire", recruitment priority
   - Brand: Reputation risk, customer satisfaction, public relations, complaints, negative feedback, "unhappy customer"
   - Low: Minimal business impact, routine communication, informational, general questions, no clear business value

5. CONFIDENCE (choose ONE):
   - Clear: Email clearly indicates function and intent, all information present, unambiguous purpose
   - Ambiguous: Some uncertainty, mixed signals, could be multiple categories, needs interpretation
   - Missing info: Insufficient information, very short email, unclear purpose, needs clarification

CLASSIFICATION RULES (FOLLOW THESE STRICTLY):
1. Read the ENTIRE email body, not just the subject line
2. Identify the PRIMARY purpose: What does the sender want?
3. Look for business signals:
   - "pricing", "quote", "cost", "purchase", "buy", "interested in" → Sales
   - "resume", "application", "job", "position", "hiring" → Hiring
   - "problem", "issue", "not working", "error", "help" → Support
   - "contract", "legal", "compliance", "terms" → Legal
   - "shipment", "delivery", "order", "logistics" → Ops
   - "partnership", "event", "promotion", "marketing" → Marketing
4. Assess urgency: Look for "urgent", "ASAP", "deadline", "soon", time constraints
5. Assess impact: Revenue (sales opportunity), Hiring (talent need), Brand (reputation risk), Low (routine)
6. Be honest about confidence: Clear = obvious purpose, Ambiguous = could be multiple things, Missing info = too vague

REAL EXAMPLES (learn from these):

Example 1:
Subject: "Enterprise Pricing Inquiry"
Body: "Hi, I'm reaching out on behalf of TechCorp. We're interested in your platform for 50+ employees. Could you provide pricing details?"
→ Sales, Inquiry, Soon, Revenue, Clear
(Why: Customer wants pricing = Sales, asking for info = Inquiry, business opportunity = Revenue)

Example 2:
Subject: "Application for Senior Developer"
Body: "I've attached my resume for the position. I have 8 years of experience..."
→ Hiring, Application, Can wait, Hiring, Clear
(Why: Job application = Hiring + Application, not urgent = Can wait, hiring need = Hiring impact)

Example 3:
Subject: "URGENT - System Down"
Body: "Our customers can't login. This is critical. Need help immediately!"
→ Support, Complaint, Immediate, Brand, Clear
(Why: Technical issue = Support, problem = Complaint, urgent language = Immediate, reputation risk = Brand)

Example 4:
Subject: "Re: Product Demo"
Body: "Just following up on my email from last week about scheduling a demo."
→ Sales, Follow-up, Soon, Revenue, Clear
(Why: Sales context = Sales, following up = Follow-up, sales opportunity = Revenue)

Example 5:
Subject: "Question about your service"
Body: "What are your business hours and support availability?"
→ Support, FAQ, Can wait, Low, Clear
(Why: Support question = Support, common question = FAQ, routine = Low impact)

Return ONLY a JSON object with these exact keys:
{{"function": "Sales", "intent": "Inquiry", "urgency": "Soon", "impact": "Revenue", "confidence": "Clear"}}"""

    messages = [
        {
            "role": "system",
            "content": "You are an expert email classification system for business communications. Always return valid JSON with the exact structure requested. Analyze business context and meaning, not just keywords. Never include markdown code blocks or explanations - only the JSON object."
        },
        {
            "role": "user",
            "content": prompt
        }
    ]
    
    try:
        # Use JSON mode for structured output
        response = await openai_client.chat_completion(
            messages=messages,
            temperature=0.3,  # Lower temperature for consistent classification
            max_tokens=300,
            response_format={"type": "json_object"}  # Force JSON output
        )
        
        # Parse JSON response
        classification = openai_client.parse_json_response(response)
        
        # Validate and set defaults
        valid_functions = ["Sales", "Hiring", "Support", "Legal", "Ops", "Marketing", "Admin"]
        valid_intents = ["Inquiry", "Follow-up", "Objection", "Scheduling", "Application", "FAQ", "Complaint"]
        valid_urgency = ["Immediate", "Soon", "Can wait"]
        valid_impact = ["Revenue", "Hiring", "Brand", "Low"]
        valid_confidence = ["Clear", "Ambiguous", "Missing info"]
        
        function = classification.get("function", "Admin")
        if function not in valid_functions:
            function = "Admin"
        
        intent = classification.get("intent", "Inquiry")
        if intent not in valid_intents:
            intent = "Inquiry"
        
        urgency = classification.get("urgency", "Can wait")
        if urgency not in valid_urgency:
            urgency = "Can wait"
        
        impact = classification.get("impact", "Low")
        if impact not in valid_impact:
            impact = "Low"
        
        confidence = classification.get("confidence", "Ambiguous")
        if confidence not in valid_confidence:
            confidence = "Ambiguous"
        
        # Log classification result for debugging
        logger.info(f"Classification result: function={function}, intent={intent}, urgency={urgency}, impact={impact}, confidence={confidence}")
        
        # Return state update
        return {
            "function": function,
            "intent": intent,
            "urgency": urgency,
            "impact": impact,
            "confidence": confidence,
            "classification_metadata": {
                "function": function,
                "intent": intent,
                "urgency": urgency,
                "impact": impact,
                "confidence": confidence
            }
        }
        
    except Exception as e:
        logger.error(f"Classification error: {str(e)}", exc_info=True)
        logger.error(f"Subject: {subject[:100]}, Body preview: {body[:200]}")
        # Fallback to defaults
        return {
            "function": "Admin",
            "intent": "Inquiry",
            "urgency": "Can wait",
            "impact": "Low",
            "confidence": "Missing info",
            "classification_metadata": {
                "function": "Admin",
                "intent": "Inquiry",
                "urgency": "Can wait",
                "impact": "Low",
                "confidence": "Missing info"
            }
        }

