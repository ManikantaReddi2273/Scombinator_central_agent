"""
Action Recommender Node - Step 5 of Flow 1
Recommends next action based on classification
"""
from typing import Dict
from services.flow1.state import Flow1State
from services.openai_client import openai_client
import logging

logger = logging.getLogger(__name__)

# Valid actions list
VALID_ACTIONS = [
    "Reply with template",
    "Ask for missing information",
    "Schedule meeting",
    "Review resume",
    "Escalate to human",
    "Hold/Ignore"
]


async def action_recommender_node(state: Flow1State) -> Dict:
    """
    Step 5: Action Recommendation
    
    Recommends the best next action based on classification.
    Applies escalation rules first, then context-based recommendations.
    
    Args:
        state: Flow1State with classification fields
        
    Returns:
        Dict with recommended_action
    """
    function = state.get("function", "Admin")
    intent = state.get("intent", "Inquiry")
    urgency = state.get("urgency", "Can wait")
    impact = state.get("impact", "Low")
    confidence = state.get("confidence", "Missing info")
    
    # Get pricing policy from brand context (if available)
    pricing_policy = ""
    brand_context = state.get("brand_context")
    if brand_context and isinstance(brand_context, dict):
        key_points = brand_context.get("key_points", {})
        if isinstance(key_points, dict):
            pricing_policy = key_points.get("pricing_policy", "")
    
    # Add pricing policy context if available
    policy_context = ""
    if pricing_policy:
        policy_context = f"\n\nCOMPANY POLICY:\n{pricing_policy}\n\nNOTE: Apply this policy when recommending actions for pricing-related inquiries.\n"
    
    # Enhanced prompt with clear decision tree
    prompt = f"""You are an action recommendation system. Based on this email classification, recommend the SINGLE BEST next action.

EMAIL CLASSIFICATION:
- Function: {function}
- Intent: {intent}
- Urgency: {urgency}
- Impact: {impact}
- Confidence: {confidence}
{policy_context}

AVAILABLE ACTIONS (choose exactly ONE):
1. "Reply with template" - Standard automated response using company email template
2. "Ask for missing information" - Need more details/clarification before responding
3. "Schedule meeting" - Requires scheduling a call, demo, or meeting
4. "Review resume" - For job applications, needs human resume review
5. "Escalate to human" - Too complex/sensitive for automated response, needs human attention
6. "Hold/Ignore" - Very low priority, can be deferred or ignored

DECISION TREE (follow in order, stop at first match):

LEVEL 1: CRITICAL ESCALATIONS (highest priority)
   ✓ Legal function → "Escalate to human" (always)
   ✓ Missing info confidence → "Ask for missing information" (always)
   ✓ Complaint + Brand impact → "Escalate to human" (reputation risk)
   ✓ Complaint + Immediate urgency → "Escalate to human" (urgent issue)
   ✓ Objection + Revenue impact → "Escalate to human" (sales risk)
   ✓ Revenue impact + Immediate urgency → "Escalate to human" (critical opportunity)

LEVEL 2: FUNCTION-SPECIFIC ACTIONS
   ✓ Hiring + Application → "Review resume" (always for applications)
   ✓ Sales + Scheduling → "Schedule meeting" (always for scheduling requests)
   ✓ Sales + Objection → "Escalate to human" (needs human negotiation)
   ✓ Support + Complaint → "Escalate to human" (customer satisfaction risk)

LEVEL 3: STANDARD RESPONSES
   ✓ Sales + Inquiry/Follow-up → "Reply with template"
   ✓ Hiring + Inquiry → "Reply with template"
   ✓ Support + Inquiry → "Reply with template"
   ✓ Marketing + Inquiry → "Reply with template"
   ✓ Ops + Inquiry → "Reply with template"

LEVEL 4: LOW PRIORITY
   ✓ Low impact + Can wait + FAQ → "Hold/Ignore"
   ✓ Admin + Can wait → "Reply with template"

LEVEL 5: DEFAULT
   ✓ If no match above → "Reply with template"

DECISION EXAMPLES:

Example 1: Legal + Inquiry + Soon + Low + Clear
   → Level 1: Legal function → "Escalate to human" ✓

Example 2: Sales + Scheduling + Soon + Revenue + Clear
   → Level 2: Sales + Scheduling → "Schedule meeting" ✓

Example 3: Hiring + Application + Can wait + Hiring + Clear
   → Level 2: Hiring + Application → "Review resume" ✓

Example 4: Support + Complaint + Immediate + Brand + Clear
   → Level 1: Complaint + Immediate → "Escalate to human" ✓

Example 5: Sales + Inquiry + Soon + Revenue + Clear
   → Level 3: Sales + Inquiry → "Reply with template" ✓

Example 6: Support + FAQ + Can wait + Low + Clear
   → Level 4: Low impact + FAQ → "Hold/Ignore" ✓

NOW DECIDE FOR THIS EMAIL:
Function: {function}, Intent: {intent}, Urgency: {urgency}, Impact: {impact}, Confidence: {confidence}

Follow the decision tree above and return the action as JSON:
{{"action": "<exact_action_text>"}}

Return ONLY the JSON object:"""

    messages = [
        {
            "role": "system",
            "content": "You are an action recommendation system for business emails. Return only a JSON object with an 'action' field containing the exact action text from the available options. Apply escalation rules first (STEP 1), then context-based recommendations (STEP 2)."
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
            temperature=0.3,  # Lower temperature for consistent recommendations
            max_tokens=50,
            response_format={"type": "json_object"}  # Force JSON output
        )
        
        # Parse JSON response
        result = openai_client.parse_json_response(response)
        action = result.get("action", "").strip()
        
        # Remove quotes if present
        if action.startswith('"') and action.endswith('"'):
            action = action[1:-1]
        elif action.startswith("'") and action.endswith("'"):
            action = action[1:-1]
        
        # Validate against known actions
        for valid_action in VALID_ACTIONS:
            if valid_action.lower() == action.lower() or valid_action.lower() in action.lower():
                return {
                    "recommended_action": valid_action
                }
        
        # If no match found, apply escalation rules manually
        if confidence == "Missing info":
            return {"recommended_action": "Ask for missing information"}
        if urgency == "Immediate" and impact == "Revenue":
            return {"recommended_action": "Escalate to human"}
        if intent == "Objection" and confidence != "Clear":
            return {"recommended_action": "Escalate to human"}
        if intent == "Complaint" and impact == "Brand":
            return {"recommended_action": "Escalate to human"}
        if function == "Legal":
            return {"recommended_action": "Escalate to human"}
        if function == "Hiring" and intent == "Application":
            return {"recommended_action": "Review resume"}
        
        # Default fallback
        return {"recommended_action": "Reply with template"}
        
    except Exception as e:
        logger.error(f"Action recommendation error: {str(e)}")
        # Apply escalation rules as fallback
        if confidence == "Missing info":
            return {"recommended_action": "Ask for missing information"}
        if urgency == "Immediate" and impact == "Revenue":
            return {"recommended_action": "Escalate to human"}
        if function == "Legal":
            return {"recommended_action": "Escalate to human"}
        return {"recommended_action": "Reply with template"}

