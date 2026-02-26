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
    
    # Get pricing policy from brand context (loaded from Redis cache via orchestrator)
    pricing_policy = ""
    brand_context = state.get("brand_context")
    if brand_context and isinstance(brand_context, dict):
        key_points = brand_context.get("key_points", {})
        if isinstance(key_points, dict):
            pricing_policy = key_points.get("pricing_policy", "")
            if pricing_policy:
                logger.info(f"Using brand context pricing policy for action recommendation")
    else:
        logger.warning("Brand context not available in state - action recommendation without pricing policy")
    
    # Add pricing policy context if available
    policy_context = ""
    if pricing_policy:
        policy_context = f"\n\nCOMPANY POLICY:\n{pricing_policy}\n\nNOTE: Apply this policy when recommending actions for pricing-related inquiries.\n"
    
    # Enhanced prompt with few-shot examples showing decision logic
    prompt = f"""You are an action recommendation system. Based on this email classification, recommend the SINGLE BEST next action.

EMAIL CLASSIFICATION:
- Function: {function}
- Intent: {intent}
- Urgency: {urgency}
- Impact: {impact}
- Confidence: {confidence}
{policy_context}

AVAILABLE ACTIONS (choose exactly ONE):
1. "Reply with template" - Standard automated response
2. "Ask for missing information" - Need more details/clarification
3. "Schedule meeting" - Requires scheduling a call, demo, or meeting
4. "Review resume" - For job applications, needs human resume review
5. "Escalate to human" - Too complex/sensitive for automated response
6. "Hold/Ignore" - Very low priority, can be deferred

DECISION RULES (apply in order, stop at first match):
1. Legal function → "Escalate to human" (always)
2. Missing info confidence → "Ask for missing information" (always)
3. Complaint + (Brand impact OR Immediate urgency) → "Escalate to human"
4. Objection + Revenue impact → "Escalate to human"
5. Revenue impact + Immediate urgency → "Escalate to human"
6. Hiring + Application → "Review resume" (always)
7. Sales + Scheduling → "Schedule meeting" (always)
8. Sales + Objection → "Escalate to human"
9. Support + Complaint → "Escalate to human"
10. Sales + Inquiry/Follow-up → "Reply with template"
11. Hiring + Inquiry → "Reply with template"
12. Support + Inquiry → "Reply with template"
13. Low impact + Can wait + FAQ → "Hold/Ignore"
14. Default → "Reply with template"

FEW-SHOT EXAMPLES:

Example 1:
Input: Legal + Inquiry + Soon + Low + Clear
Reasoning: Legal function → Rule 1 applies
Output: {{"action": "Escalate to human"}}

Example 2:
Input: Sales + Scheduling + Soon + Revenue + Clear
Reasoning: Sales + Scheduling → Rule 7 applies
Output: {{"action": "Schedule meeting"}}

Example 3:
Input: Hiring + Application + Can wait + Hiring + Clear
Reasoning: Hiring + Application → Rule 6 applies
Output: {{"action": "Review resume"}}

Example 4:
Input: Support + Complaint + Immediate + Brand + Clear
Reasoning: Complaint + Immediate urgency → Rule 3 applies
Output: {{"action": "Escalate to human"}}

Example 5:
Input: Sales + Inquiry + Soon + Revenue + Clear
Reasoning: Sales + Inquiry → Rule 10 applies
Output: {{"action": "Reply with template"}}

Example 6:
Input: Support + FAQ + Can wait + Low + Clear
Reasoning: Low impact + Can wait + FAQ → Rule 13 applies
Output: {{"action": "Hold/Ignore"}}

Example 7:
Input: Sales + Objection + Soon + Revenue + Clear
Reasoning: Objection + Revenue impact → Rule 4 applies
Output: {{"action": "Escalate to human"}}

Example 8:
Input: Admin + Inquiry + Can wait + Low + Clear
Reasoning: No specific rule matches → Rule 14 (Default) applies
Output: {{"action": "Reply with template"}}

Example 9:
Input: Marketing + Inquiry + Soon + Low + Ambiguous
Reasoning: Missing info confidence → Rule 2 applies
Output: {{"action": "Ask for missing information"}}

NOW DECIDE FOR THIS EMAIL:
Function: {function}, Intent: {intent}, Urgency: {urgency}, Impact: {impact}, Confidence: {confidence}

Apply the decision rules and return:
{{"action": "<exact_action_text>"}}"""

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

