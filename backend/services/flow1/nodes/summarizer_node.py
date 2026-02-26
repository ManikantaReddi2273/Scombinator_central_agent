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
    
    # Truncate body to 1500 chars for context
    body_truncated = body[:1500] if len(body) > 1500 else body
    
    # Add thread context note if this is a follow-up
    thread_note = ""
    if thread_count > 0:
        thread_note = f"\nNOTE: This is a follow-up email ({thread_count + 1}rd/{(thread_count + 1)}th in thread). Consider conversation context."
    
    # Enhanced prompt with few-shot examples aligned with blueprint
    prompt = f"""Create an executive summary (1-2 sentences, max 150 chars) that explains WHAT THIS EMAIL MEANS FOR THE BUSINESS and WHAT ACTION IS NEEDED. Explain business meaning, NOT email content.

COMPANY: {company_name}
EMAIL: {subject}
BODY: {body_truncated}
CLASSIFIED: {function} / {intent}
{thread_note}

REQUIREMENTS:
- 1-2 sentences, max 150 characters
- Format: "[Business Context] - [Required Action]"
- NO quotes, NO paraphrasing, NO "the email says"
- Direct, professional, executive-ready

FEW-SHOT EXAMPLES:

Example 1:
Input:
Subject: "Enterprise Pricing Inquiry"
Body: "Hi, I'm reaching out on behalf of TechCorp. We're interested in your platform for 50+ employees. Could you provide pricing details?"
Output: Enterprise customer requesting pricing for 50+ users - needs pricing proposal and sales call

Example 2:
Input:
Subject: "Application for Senior Developer"
Body: "I've attached my resume for the position. I have 8 years of experience in Python and React."
Output: Senior developer candidate submitted resume for open position - requires technical review and interview scheduling

Example 3:
Input:
Subject: "URGENT - System Down"
Body: "Our customers can't login. This is critical. Need help immediately!"
Output: Customer reporting critical login failure affecting multiple users - needs immediate technical support escalation

Example 4:
Input:
Subject: "Re: Product Demo"
Body: "Just following up on my email from last week about scheduling a demo. Any update?"
Output: Prospect following up on product demo request from last week - needs scheduling confirmation and preparation

Example 5:
Input:
Subject: "Contract Review Needed"
Body: "We need to review the data processing agreement before signing. Can you clarify section 3.2?"
Output: Legal team inquiry about data processing agreement terms - requires compliance review and contract clarification

Example 6:
Input:
Subject: "Too expensive"
Body: "Your pricing is too high compared to competitors. We're looking elsewhere."
Output: Potential client expressing pricing concerns and comparing to competitor - needs value proposition and negotiation

Example 7:
Input:
Subject: "Question about remote work"
Body: "I'm interested in the engineering role. Do you offer remote work options?"
Output: Job applicant asking about remote work policy for engineering role - needs HR policy clarification

Example 8:
Input:
Subject: "Order #12345 Status"
Body: "Hi, can you check the status of my order? It was supposed to arrive yesterday."
Output: Customer inquiring about delayed order delivery - needs order status update and resolution

NOW CREATE SUMMARY FOR THIS EMAIL:
Subject: {subject}
Body: {body_truncated}
Classified: {function} / {intent}

Return ONLY the summary text (max 150 chars):"""

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

