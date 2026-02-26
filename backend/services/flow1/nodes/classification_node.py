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
    
    # Get company name from brand context (loaded from Redis cache via orchestrator)
    company_name = "Company"
    brand_context = state.get("brand_context")
    if brand_context and isinstance(brand_context, dict):
        key_points = brand_context.get("key_points", {})
        if isinstance(key_points, dict):
            company_name = key_points.get("company_name", "Company")
            logger.info(f"Using brand context company_name: {company_name}")
    else:
        logger.warning("Brand context not available in state - using default company name")
    
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
    
    # Enhanced prompt with few-shot examples aligned with architecture
    prompt = f"""You are an expert business email classifier for {company_name}. Analyze this email across 5 dimensions. Read the ENTIRE email body, not just the subject.

EMAIL TO CLASSIFY:
Subject: {subject}
Body: {body_truncated}
{thread_context}

CLASSIFICATION DIMENSIONS:

1. FUNCTION (choose ONE):
   - Sales: Products/services, pricing, purchasing, demos, quotes, proposals
   - Hiring: Job applications, resumes, recruitment, candidate communications
   - Support: Technical issues, bug reports, help requests, troubleshooting
   - Legal: Contracts, compliance, legal matters, terms, disputes
   - Ops: Operations, logistics, shipping, fulfillment, delivery, order status
   - Marketing: Promotions, campaigns, partnerships, events, newsletters
   - Admin: General admin tasks, billing, account management (LAST RESORT)

2. INTENT (choose ONE):
   - Inquiry: Initial question, information request
   - Follow-up: Following up on previous conversation, checking status
   - Objection: Concerns, hesitations, pushback
   - Scheduling: Requesting meetings, calls, appointments
   - Application: Job application submission, resume attached
   - FAQ: Frequently asked question, common query
   - Complaint: Unhappy customer, dissatisfaction, issue escalation

3. URGENCY (choose ONE):
   - Immediate: "urgent", "ASAP", "emergency", "critical", "deadline today"
   - Soon: "this week", "by Friday", "need response soon", time-sensitive
   - Can wait: Standard response time, no deadline, routine inquiry

4. IMPACT (choose ONE):
   - Revenue: Direct sales impact, potential deals, pricing inquiries
   - Hiring: Talent acquisition, critical role filling, senior positions
   - Brand: Reputation risk, customer satisfaction, complaints
   - Low: Minimal business impact, routine communication

5. CONFIDENCE (choose ONE):
   - Clear: Email clearly indicates function and intent
   - Ambiguous: Some uncertainty, mixed signals
   - Missing info: Insufficient information, very short email

FEW-SHOT EXAMPLES (follow this exact format):

Example 1:
Input:
Subject: "Enterprise Pricing Inquiry"
Body: "Hi, I'm reaching out on behalf of TechCorp. We're interested in your platform for 50+ employees. Could you provide pricing details?"
Output: {{"function": "Sales", "intent": "Inquiry", "urgency": "Soon", "impact": "Revenue", "confidence": "Clear"}}
Reasoning: Customer wants pricing = Sales, asking for info = Inquiry, business opportunity = Revenue impact

Example 2:
Input:
Subject: "Application for Senior Developer"
Body: "I've attached my resume for the position. I have 8 years of experience in Python and React."
Output: {{"function": "Hiring", "intent": "Application", "urgency": "Can wait", "impact": "Hiring", "confidence": "Clear"}}
Reasoning: Job application = Hiring + Application, not urgent = Can wait, hiring need = Hiring impact

Example 3:
Input:
Subject: "URGENT - System Down"
Body: "Our customers can't login. This is critical. Need help immediately!"
Output: {{"function": "Support", "intent": "Complaint", "urgency": "Immediate", "impact": "Brand", "confidence": "Clear"}}
Reasoning: Technical issue = Support, problem = Complaint, urgent language = Immediate, reputation risk = Brand

Example 4:
Input:
Subject: "Re: Product Demo"
Body: "Just following up on my email from last week about scheduling a demo. Any update?"
Output: {{"function": "Sales", "intent": "Follow-up", "urgency": "Soon", "impact": "Revenue", "confidence": "Clear"}}
Reasoning: Sales context = Sales, following up = Follow-up, sales opportunity = Revenue

Example 5:
Input:
Subject: "Question about your service"
Body: "What are your business hours and support availability?"
Output: {{"function": "Support", "intent": "FAQ", "urgency": "Can wait", "impact": "Low", "confidence": "Clear"}}
Reasoning: Support question = Support, common question = FAQ, routine = Low impact

Example 6:
Input:
Subject: "Contract Review Needed"
Body: "We need to review the data processing agreement before signing. Can you clarify section 3.2?"
Output: {{"function": "Legal", "intent": "Inquiry", "urgency": "Soon", "impact": "Low", "confidence": "Clear"}}
Reasoning: Contract/agreement = Legal, asking for clarification = Inquiry, legal matter = Low impact (not revenue)

Example 7:
Input:
Subject: "Order #12345 Status"
Body: "Hi, can you check the status of my order? It was supposed to arrive yesterday."
Output: {{"function": "Ops", "intent": "Inquiry", "urgency": "Soon", "impact": "Brand", "confidence": "Clear"}}
Reasoning: Order status = Ops, asking for info = Inquiry, delivery issue = Brand impact (customer satisfaction)

Example 8:
Input:
Subject: "Too expensive"
Body: "Your pricing is too high compared to competitors. We're looking elsewhere."
Output: {{"function": "Sales", "intent": "Objection", "urgency": "Soon", "impact": "Revenue", "confidence": "Clear"}}
Reasoning: Pricing concern = Sales, objection = Objection, sales risk = Revenue impact

NOW CLASSIFY THIS EMAIL:
Subject: {subject}
Body: {body_truncated}

Return ONLY a JSON object with these exact keys:
{{"function": "...", "intent": "...", "urgency": "...", "impact": "...", "confidence": "..."}}"""

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

