"""
Summarizer Node - Step 4 of Flow 1
Generates zero-context executive summary (meaning not content)
"""
from typing import Dict
from services.flow1.state import Flow1State
from services.openai_client import openai_client
import logging

logger = logging.getLogger(__name__)


async def summarizer_node(state: Flow1State) -> Dict:
    """
    Step 4: Zero-Context Executive Summary
    
    Generates 1-2 line summary that explains MEANING, not content.
    No quotes, no fluff, executive-ready.
    
    Args:
        state: Flow1State with email data and classification
        
    Returns:
        Dict with executive_summary
    """
    subject = state.get("email_subject", "")
    body = state.get("email_body", "")
    function = state.get("function", "Admin")
    intent = state.get("intent", "Inquiry")
    thread_count = state.get("thread_count", 0)
    
    # Get company name from brand context (if available)
    company_name = "Company"
    brand_context = state.get("brand_context")
    if brand_context and isinstance(brand_context, dict):
        key_points = brand_context.get("key_points", {})
        if isinstance(key_points, dict):
            company_name = key_points.get("company_name", "Company")
    
    # Truncate body to 1500 chars for context
    body_truncated = body[:1500] if len(body) > 1500 else body
    
    # Add thread context note if this is a follow-up
    thread_note = ""
    if thread_count > 0:
        thread_note = f"\nNOTE: This is a follow-up email ({thread_count + 1}rd/{(thread_count + 1)}th in thread). Consider conversation context."
    
    # Enhanced prompt with better examples and structure
    prompt = f"""Create an executive summary that explains WHAT THIS EMAIL MEANS FOR THE BUSINESS and WHAT ACTION IS NEEDED. Do NOT quote or paraphrase the email content.

COMPANY CONTEXT:
Company: {company_name}

EMAIL DETAILS:
Subject: {subject}
Body: {body_truncated}
Classified as: {function} / {intent}
{thread_note}

SUMMARY REQUIREMENTS:
1. Length: Exactly 1-2 sentences, maximum 150 characters (strict limit)
2. Format: Start with business context, end with required action
3. Style: Direct, professional, executive-ready
4. Content: Explain business meaning, NOT email content
5. NO quotes, NO paraphrasing, NO "the email says"

GOOD SUMMARY STRUCTURE:
"[Business Context] - [Required Action]"

EXCELLENT EXAMPLES (copy this style):

✓ "Enterprise customer requesting pricing for 100+ users - needs pricing proposal and sales call"
✓ "Senior developer candidate submitted resume for open position - requires technical review and interview scheduling"
✓ "Customer reporting critical login failure affecting multiple users - needs immediate technical support escalation"
✓ "Prospect following up on product demo request from last week - needs scheduling confirmation and preparation"
✓ "Follow-up email (3rd in thread) - customer asking about implementation timeline after pricing discussion"
✓ "Legal team inquiry about data processing agreement terms - requires compliance review and contract clarification"
✓ "Potential client expressing pricing concerns and comparing to competitor - needs value proposition and negotiation"
✓ "Job applicant asking about remote work policy for engineering role - needs HR policy clarification"

BAD EXAMPLES (avoid these patterns):
✗ "The email says they want pricing" (quotes content)
✗ "Customer wrote that they are interested" (paraphrases content)
✗ "According to the email, they need help" (references email)
✗ "They mentioned a job application" (paraphrases)
✗ "Email about pricing inquiry" (too vague, no action)

YOUR TASK:
Analyze this email and write a summary following the GOOD examples above. Focus on:
- WHO is contacting (customer, candidate, partner, etc.)
- WHAT business need they represent (sales opportunity, hiring need, support issue, etc.)
- WHAT action is required (proposal, review, escalation, scheduling, etc.)

Write the summary now (max 150 chars, business-meaning focused):"""

    messages = [
        {
            "role": "system",
            "content": "You are an executive summary writer. Create concise, actionable summaries that explain business meaning, not content. Never quote from emails. Never use phrases like 'the email says' or 'they wrote'. Maximum 150 characters. Start directly with the business meaning."
        },
        {
            "role": "user",
            "content": prompt
        }
    ]
    
    try:
        response = await openai_client.chat_completion(
            messages=messages,
            temperature=0.5,  # Balanced for creativity and consistency
            max_tokens=100
        )
        
        summary = response.strip()
        
        # Remove quotes if present
        if summary.startswith('"') and summary.endswith('"'):
            summary = summary[1:-1]
        elif summary.startswith("'") and summary.endswith("'"):
            summary = summary[1:-1]
        
        # Remove common content-focused phrases
        content_phrases = [
            "The email says",
            "The email indicates",
            "According to the email",
            "The customer wrote",
            "They mentioned",
            "The email mentions",
            "They said"
        ]
        for phrase in content_phrases:
            if summary.lower().startswith(phrase.lower()):
                summary = summary[len(phrase):].strip()
                # Remove leading colon or dash if present
                if summary.startswith(":") or summary.startswith("-"):
                    summary = summary[1:].strip()
        
        # Ensure max length
        if len(summary) > 150:
            summary = summary[:147] + "..."
        
        # Ensure it's not empty
        if not summary or len(summary.strip()) == 0:
            summary = f"{function} {intent} - needs response"
        
        return {
            "executive_summary": summary
        }
        
    except Exception as e:
        logger.error(f"Summary generation error: {str(e)}")
        # Fallback summary
        return {
            "executive_summary": f"{function} {intent} - needs response"
        }

