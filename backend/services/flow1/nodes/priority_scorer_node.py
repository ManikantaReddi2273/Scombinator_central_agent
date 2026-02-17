"""
Priority Scorer Node - Step 3 of Flow 1
Converts classification to numeric priority score (0-100)
"""
from typing import Dict
from services.flow1.state import Flow1State
from services.openai_client import openai_client
import logging

logger = logging.getLogger(__name__)


async def priority_scorer_node(state: Flow1State) -> Dict:
    """
    Step 3: Priority Scoring
    
    Converts classification signals into numeric priority score (0-100)
    Applies company context and business rules.
    
    Args:
        state: Flow1State with classification fields
        
    Returns:
        Dict with priority_score
    """
    function = state.get("function", "Admin")
    intent = state.get("intent", "Inquiry")
    urgency = state.get("urgency", "Can wait")
    impact = state.get("impact", "Low")
    confidence = state.get("confidence", "Missing info")
    thread_count = state.get("thread_count", 0)
    
    # Get SLA rules from brand context (if available)
    sla_rules = ""
    brand_context = state.get("brand_context")
    if brand_context and isinstance(brand_context, dict):
        key_points = brand_context.get("key_points", {})
        if isinstance(key_points, dict):
            sla_rules = key_points.get("sla_rules", "")
    
    # Add thread context note if this is part of an ongoing conversation
    thread_note = ""
    if thread_count > 0:
        thread_note = f"\n- Thread Context: This is email #{thread_count + 1} in an ongoing conversation (thread_count={thread_count})"
        thread_note += "\n  NOTE: Ongoing conversations may warrant slightly higher priority. Add 2-5 points if this is a follow-up in an active thread."
    
    # Add SLA rules context if available
    sla_context = ""
    if sla_rules:
        sla_context = f"\n\nCOMPANY SLA RULES (apply these when calculating priority):\n{sla_rules}\n"
    
    # Enhanced prompt with explicit calculation steps
    prompt = f"""Calculate a priority score (0-100) for this email. Use the scoring formula below and return the EXACT calculated number.

EMAIL CLASSIFICATION:
- Function: {function}
- Intent: {intent}
- Urgency: {urgency}
- Impact: {impact}
- Confidence: {confidence}
{thread_note}
{sla_context}

SCORING FORMULA (calculate step by step):

STEP 1: Base Score from Impact
   - Revenue impact → Start with 75
   - Hiring impact → Start with 65
   - Brand impact → Start with 55
   - Low impact → Start with 25

STEP 2: Add Urgency Points
   - Immediate → Add 20 points
   - Soon → Add 10 points
   - Can wait → Add 0 points

STEP 3: Add Intent Points
   - Complaint → Add 15 points
   - Objection → Add 15 points
   - Application (only if Hiring) → Add 10 points
   - Scheduling → Add 5 points
   - Inquiry → Add 5 points
   - Follow-up → Add 0 points
   - FAQ → Subtract 5 points

STEP 4: Apply Confidence Penalty
   - Clear → No change (0 points)
   - Ambiguous → Subtract 5 points
   - Missing info → Subtract 10 points

STEP 5: Special Multipliers (apply after all additions)
   - Legal function → Multiply final score by 1.15 (max 100)
   - Support + Complaint → Add 10 bonus points
   - Sales + Revenue + Immediate → Set to 95-100 range
   - Support + Complaint + Immediate → Set to 90-100 range

STEP 6: Final Clamp
   - Ensure score is between 0 and 100
   - Round to nearest integer

CALCULATION EXAMPLES:

Example 1: Sales + Inquiry + Soon + Revenue + Clear
   Base: 75 (Revenue)
   + Urgency: +10 (Soon) = 85
   + Intent: +5 (Inquiry) = 90
   + Confidence: 0 (Clear) = 90
   Final: 90

Example 2: Support + Complaint + Immediate + Brand + Clear
   Base: 55 (Brand)
   + Urgency: +20 (Immediate) = 75
   + Intent: +15 (Complaint) = 90
   + Confidence: 0 (Clear) = 90
   + Special: +10 (Support+Complaint) = 100
   Final: 100

Example 3: Hiring + Application + Soon + Hiring + Clear
   Base: 65 (Hiring)
   + Urgency: +10 (Soon) = 75
   + Intent: +10 (Application) = 85
   + Confidence: 0 (Clear) = 85
   Final: 85

Example 4: Support + FAQ + Can wait + Low + Clear
   Base: 25 (Low)
   + Urgency: +0 (Can wait) = 25
   + Intent: -5 (FAQ) = 20
   + Confidence: 0 (Clear) = 20
   Final: 20

Example 5: Legal + Inquiry + Soon + Low + Clear
   Base: 25 (Low)
   + Urgency: +10 (Soon) = 35
   + Intent: +5 (Inquiry) = 40
   + Confidence: 0 (Clear) = 40
   + Special: ×1.15 = 46
   Final: 46

NOW CALCULATE FOR THIS EMAIL:
Function: {function}, Intent: {intent}, Urgency: {urgency}, Impact: {impact}, Confidence: {confidence}

Show your calculation and return the final score as JSON:
{{"score": <calculated_number>}}

Return ONLY the JSON object with the calculated score:"""

    messages = [
        {
            "role": "system",
            "content": "You are a priority scoring system for business emails. Return only a JSON object with a 'score' field (0-100) based on business impact and urgency. Apply the scoring rules deterministically."
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
            temperature=0.1,  # Very low temperature for deterministic scoring
            max_tokens=200,  # Increased to allow calculation explanation
            response_format={"type": "json_object"}  # Force JSON output
        )
        
        # Parse JSON response
        result = openai_client.parse_json_response(response)
        
        # Extract score
        score = result.get("score", None)
        
        # If score is missing or invalid, calculate it manually using the same formula
        if score is None:
            logger.warning("Score not found in response, calculating manually")
            score = _calculate_priority_score(function, intent, urgency, impact, confidence)
        else:
            # Validate and clamp to 0-100 range
            try:
                score = int(float(score))
                score = max(0, min(100, score))
            except (ValueError, TypeError):
                logger.warning(f"Invalid score format: {score}, calculating manually")
                score = _calculate_priority_score(function, intent, urgency, impact, confidence)
        
        # Add small boost for ongoing conversations (thread context)
        if thread_count > 0:
            score = min(100, score + 3)  # Add 3 points for ongoing thread, cap at 100
        
        logger.info(f"Priority score calculated: {score} (Function: {function}, Intent: {intent}, Urgency: {urgency}, Impact: {impact}, Thread Count: {thread_count})")
        
        return {
            "priority_score": score
        }
        
    except Exception as e:
        logger.error(f"Priority scoring error: {str(e)}")
        # Calculate manually as fallback
        score = _calculate_priority_score(function, intent, urgency, impact, confidence)
        
        # Add small boost for ongoing conversations (thread context)
        if thread_count > 0:
            score = min(100, score + 3)  # Add 3 points for ongoing thread, cap at 100
        
        return {
            "priority_score": score
        }


def _calculate_priority_score(function: str, intent: str, urgency: str, impact: str, confidence: str) -> int:
    """
    Calculate priority score manually using the same formula as the prompt
    This serves as a fallback if OpenAI doesn't return a valid score
    """
    # STEP 1: Base Score from Impact
    if impact == "Revenue":
        score = 75
    elif impact == "Hiring":
        score = 65
    elif impact == "Brand":
        score = 55
    else:  # Low
        score = 25
    
    # STEP 2: Add Urgency Points
    if urgency == "Immediate":
        score += 20
    elif urgency == "Soon":
        score += 10
    # Can wait adds 0
    
    # STEP 3: Add Intent Points
    if intent == "Complaint":
        score += 15
    elif intent == "Objection":
        score += 15
    elif intent == "Application" and function == "Hiring":
        score += 10
    elif intent == "Scheduling":
        score += 5
    elif intent == "Inquiry":
        score += 5
    elif intent == "FAQ":
        score -= 5
    # Follow-up adds 0
    
    # STEP 4: Apply Confidence Penalty
    if confidence == "Ambiguous":
        score -= 5
    elif confidence == "Missing info":
        score -= 10
    # Clear has no penalty
    
    # STEP 5: Special Multipliers
    if function == "Legal":
        score = int(score * 1.15)
    elif function == "Support" and intent == "Complaint":
        score += 10
    elif function == "Sales" and impact == "Revenue" and urgency == "Immediate":
        score = max(95, score)  # Ensure high score for critical sales
    
    # STEP 6: Final Clamp
    score = max(0, min(100, score))
    
    return score

