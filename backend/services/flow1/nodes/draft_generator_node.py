"""
Draft Generator Node - Step 6 of Flow 1
Generates editable email draft using company templates and brand tone
"""
from typing import Dict
from services.flow1.state import Flow1State
from services.openai_client import openai_client
from services.policy_loader import policy_loader_service
import logging

logger = logging.getLogger(__name__)

logger = logging.getLogger(__name__)


def _clean_draft_body(body: str) -> str:
    """
    Clean up draft body to remove markdown, instructions, and meta-commentary
    
    Args:
        body: Raw draft body from AI
        
    Returns:
        Cleaned email body text
    """
    # Remove markdown code blocks
    if "```" in body:
        lines = body.split('\n')
        cleaned_lines = []
        in_code_block = False
        for line in lines:
            if line.strip().startswith("```"):
                in_code_block = not in_code_block
                continue
            if not in_code_block:
                cleaned_lines.append(line)
        body = '\n'.join(cleaned_lines)
    
    # Remove common instruction patterns
    instruction_patterns = [
        "Here's a professional",
        "Here is a professional",
        "Here's an email",
        "Here is an email",
        "**Subject:**",
        "**Notes on",
        "**Optional additions",
        "---",
        "Notes:",
        "Guidelines:",
        "Requirements:",
        "tailored for a",
        "assuming a",
        "brand voice",
        "**sales function**",
        "**helpful, concise",
    ]
    
    lines = body.split('\n')
    cleaned_lines = []
    skip_until_blank = False
    
    for line in lines:
        line_lower = line.lower().strip()
        
        # Skip lines that are clearly instructions or meta-commentary
        if any(pattern.lower() in line_lower for pattern in instruction_patterns):
            skip_until_blank = True
            continue
        
        # Skip lines with markdown formatting indicators
        if line.strip().startswith("**") and line.strip().endswith("**"):
            # Might be a heading, check if it's content or instruction
            if any(word in line_lower for word in ["subject", "notes", "guidelines", "requirements", "optional"]):
                skip_until_blank = True
                continue
        
        # If we hit a blank line after instructions, reset
        if skip_until_blank and not line.strip():
            skip_until_blank = False
            continue
        
        if not skip_until_blank:
            # Remove markdown bold/italic but keep the text
            cleaned_line = line.replace("**", "").replace("*", "").replace("---", "")
            cleaned_lines.append(cleaned_line)
    
    body = '\n'.join(cleaned_lines)
    
    # Remove placeholders
    body = body.replace("[Your Name]", "")
    body = body.replace("[Your Company Name]", "")
    body = body.replace("[Your Job Title]", "")
    body = body.replace("[Your Direct Phone Number]", "")
    body = body.replace("[Your Email Address]", "")
    body = body.replace("[Company Website]", "")
    body = body.replace("[Your Full Name]", "")
    
    # Clean up multiple blank lines
    while "\n\n\n" in body:
        body = body.replace("\n\n\n", "\n\n")
    
    # Remove leading/trailing whitespace
    body = body.strip()
    
    # Don't return fallback here - let the caller handle it
    # This function should only clean, not replace content
    return body


async def draft_generator_node(state: Flow1State, config=None) -> Dict:
    """
    Step 6: Draft Generation
    
    Generates editable email draft using company-specific templates and brand tone.
    Only generates draft if recommended_action is "Reply with template".
    
    Args:
        state: Flow1State with email data, classification, and recommended_action
        config: LangGraph config (optional, may contain 'db' session)
        
    Returns:
        Dict with draft_subject, draft_body, template_used, variables_used
    """
    # Generate draft for multiple action types, not just "Reply with template"
    recommended_action = state.get("recommended_action")
    
    # Only skip draft generation for these actions
    skip_draft_actions = ["Escalate to human", "Hold/Ignore", "Review resume"]
    if recommended_action in skip_draft_actions:
        return {
            "draft_subject": None,
            "draft_body": None,
            "template_used": None,
            "variables_used": None
        }
    
    # Generate draft for: "Reply with template", "Ask for missing information", "Schedule meeting"
    
    company_id = state.get("company_id")
    email_subject = state.get("email_subject", "")
    email_body = state.get("email_body", "")
    from_email = state.get("from_email", "")
    function = state.get("function", "Admin")
    intent = state.get("intent", "Inquiry")
    thread_history = state.get("thread_history", [])  # Always a list
    thread_count = state.get("thread_count", 0)  # Always an int
    
    # Get company templates and brand tone for context
    templates = {}
    brand_tone = None
    
    # Extract db from config if available
    db = None
    if config and isinstance(config, dict):
        db = config.get("db")
    
    if db and company_id:
        try:
            templates = await policy_loader_service.get_templates(db, company_id)
            brand_tone = await policy_loader_service.get_brand_tone(db, company_id)
        except Exception as e:
            logger.warning(f"Error loading company templates for {company_id}: {str(e)}")
            # Continue with defaults
    
    # Build context from templates if available
    template_context = ""
    if templates:
        template_names = list(templates.keys())[:5]  # Limit to first 5 for context
        template_context = f"\n\nAvailable company templates for reference: {', '.join(template_names)}"
        # Include a sample template if available
        if "general_response_template.txt" in templates:
            sample_template = templates["general_response_template.txt"][:200]  # First 200 chars
            template_context += f"\n\nSample template structure:\n{sample_template}"
    
    tone_context = f"\n\nBrand tone to match: {brand_tone}" if brand_tone else ""
    
    # Truncate email body for context
    body_truncated = email_body[:2000] if len(email_body) > 2000 else email_body
    
    # Build thread context if available
    thread_context = ""
    if len(thread_history) > 0:
        thread_context = "\n\nCONVERSATION HISTORY (previous emails in this thread - read these to understand context):\n"
        for i, prev_email in enumerate(thread_history, 1):
            thread_context += f"\n--- Previous Email {i} ---\n"
            thread_context += f"Subject: {prev_email.get('subject', 'N/A')}\n"
            thread_context += f"From: {prev_email.get('from_email', 'N/A')}\n"
            thread_context += f"Body: {prev_email.get('body', 'N/A')}\n"
        
        thread_context += "\n\nCRITICAL: Your response should:\n"
        thread_context += "- Reference previous conversation points naturally\n"
        thread_context += "- Continue the discussion without repeating information already shared\n"
        thread_context += "- Acknowledge any previous responses if relevant\n"
        thread_context += "- Build on what was already discussed\n"
        thread_context += "- Don't repeat information that was already provided in previous emails\n"
    
    # Enhanced prompt with action-specific instructions
    action_guidance = ""
    if recommended_action == "Ask for missing information":
        action_guidance = """
ACTION TYPE: Ask for Missing Information
- Politely request the specific information needed
- Be clear about what details are missing
- Explain why the information is needed
- Offer to help once information is received"""
    elif recommended_action == "Schedule meeting":
        action_guidance = """
ACTION TYPE: Schedule Meeting
- Acknowledge the meeting request
- Suggest 2-3 specific time options
- Ask for their preference or availability
- Include meeting purpose/agenda if relevant"""
    else:  # Reply with template
        action_guidance = """
ACTION TYPE: Standard Response
- Address their inquiry directly
- Provide helpful information
- Include next steps or call-to-action
- Be professional and friendly"""
    
    # Optimized prompt with better structure and specific instructions
    prompt = f"""You are a professional email writer. Write a COMPLETE, DETAILED email response that directly addresses the sender's inquiry. This email will be sent to a real person - make it helpful, specific, and actionable.

ORIGINAL EMAIL RECEIVED:
Subject: {email_subject}
From: {from_email}
Body: {body_truncated}
{thread_context}

EMAIL CONTEXT:
- Business Function: {function}
- Email Intent: {intent}
- Recommended Action: {recommended_action}
{tone_context}
{template_context}
{action_guidance}

CRITICAL INSTRUCTIONS:
1. READ THE ORIGINAL EMAIL CAREFULLY - What specific question or request did they make?
2. ADDRESS THEIR ACTUAL QUESTION - Don't give a generic response. Answer what they asked.
3. BE SPECIFIC AND HELPFUL - Provide real information, not vague promises
4. INCLUDE NEXT STEPS - What happens next? What should they do?
5. MINIMUM 3-4 PARAGRAPHS - This should be a substantial, helpful response

WRITING REQUIREMENTS:

1. STRUCTURE (include all parts):
   - Professional greeting (Hi/Hello [Name if available], or "Hello" if name unknown)
   - Opening: Acknowledge their email/inquiry
   - Body: Address their question/request (2-3 paragraphs)
   - Closing: Professional sign-off (Best regards, Sincerely, etc.)

2. CONTENT GUIDELINES:
   - Address their specific question or request from the original email
   - Be helpful, clear, and professional
   - Match the brand tone: {brand_tone if brand_tone else 'professional and friendly'}
   - Keep total length: 3-5 paragraphs (concise but complete)

3. FUNCTION-SPECIFIC TONE:
   - Sales: Helpful, informative, suggest next steps, include value proposition
   - Hiring: Professional, acknowledge application, set clear expectations, mention timeline
   - Support: Empathetic, solution-focused, offer help, provide next steps
   - Legal: Formal, refer to appropriate channels, professional boundaries
   - Marketing: Engaging, informative, highlight benefits
   - Ops: Clear, action-oriented, provide status/next steps

4. FORBIDDEN (do NOT include):
   - Markdown formatting (**, ---, #, etc.)
   - Code blocks or instructions
   - Placeholders like [Your Name], [Company Name]
   - Meta-commentary or notes
   - Explanations about the email itself
   - "Here's a response" or similar phrases

5. OUTPUT FORMAT:
   - Plain text only
   - No quotes around the text
   - No markdown
   - Ready to send directly

EXAMPLE FOR SALES PRICING INQUIRY:
Hello,

Thank you for reaching out about enterprise pricing for your team of 50+ employees. I'd be happy to provide you with detailed pricing information and help you understand how our platform can meet your needs.

Our enterprise pricing is customized based on your specific requirements, including the number of users, features needed, and any integrations. For a team of your size, we typically offer volume discounts and can provide flexible payment terms.

I'd like to schedule a brief call this week to discuss your specific needs in detail. This will help me prepare a tailored proposal that includes:
- Detailed pricing breakdown
- Feature comparison with our standard plan
- Available integrations for your tech stack
- Implementation timeline and support options

Would Tuesday or Wednesday afternoon work for you? I can also send you our enterprise pricing guide in the meantime if you'd prefer to review it first.

Looking forward to speaking with you.

Best regards

NOW WRITE THE EMAIL RESPONSE:
Based on the original email above, write a COMPLETE, DETAILED response that:
- Directly answers their specific question/request
- Provides helpful, actionable information
- Includes clear next steps
- Is at least 3-4 paragraphs long
- Sounds professional and helpful

Return ONLY the email body text, nothing else:"""

    messages = [
        {
            "role": "system",
            "content": "You are a professional email writer. Return ONLY the email body text - plain text, no markdown, no explanations, no instructions, no notes, no code blocks. Just the email content that can be sent directly. Never include meta-commentary or formatting instructions."
        },
        {
            "role": "user",
            "content": prompt
        }
    ]
    
    try:
        response = await openai_client.chat_completion(
            messages=messages,
            temperature=0.8,  # Higher temperature for natural, varied responses
            max_tokens=800  # Increased for longer, more complete responses
        )
        
        draft_body = response.strip()
        
        # Log raw response for debugging
        logger.debug(f"Draft generator raw response length: {len(draft_body)}")
        
        # Clean up the response - remove any meta-commentary, instructions, or markdown
        draft_body = _clean_draft_body(draft_body)
        
        # Validate draft quality - if too short or generic, try again or enhance
        if len(draft_body) < 100 or draft_body.lower().strip() in [
            "thank you for your email. we'll get back to you soon.",
            "thank you for your email.",
            "we'll get back to you soon."
        ]:
            logger.warning(f"Draft too short or generic ({len(draft_body)} chars), enhancing...")
            # Enhance the draft with more context
            draft_body = _enhance_draft(draft_body, email_subject, email_body, function, intent, recommended_action)
        
        # Apply brand tone adjustments if needed (additional refinement)
        if brand_tone:
            tone_lower = brand_tone.lower()
            if "formal" in tone_lower:
                draft_body = draft_body.replace("Hi ", "Hello ").replace("Thanks", "Thank you")
            elif "casual" in tone_lower or "friendly" in tone_lower:
                draft_body = draft_body.replace("Hello ", "Hi ").replace("Sincerely", "Best regards")
            elif "short" in tone_lower or "brief" in tone_lower:
                # Keep only first 3-4 paragraphs
                paragraphs = [p.strip() for p in draft_body.split('\n\n') if p.strip()]
                draft_body = '\n\n'.join(paragraphs[:4])
        
        # Final validation - ensure draft is substantial
        if len(draft_body.strip()) < 50:
            logger.error("Draft still too short after processing, using enhanced fallback")
            draft_body = _enhance_draft("", email_subject, email_body, function, intent, recommended_action)
        
        draft_subject = f"Re: {email_subject}"
        
        logger.info(f"Draft generated successfully: {len(draft_body)} characters, function={function}, intent={intent}")
        
        return {
            "draft_subject": draft_subject,
            "draft_body": draft_body,
            "template_used": "openai_generated",
            "variables_used": {}
        }
        
    except Exception as e:
        logger.error(f"Draft generation error: {str(e)}", exc_info=True)
        # Enhanced fallback that's context-aware
        draft_body = _enhance_draft("", email_subject, email_body, function, intent, recommended_action)
        return {
            "draft_subject": f"Re: {email_subject}",
            "draft_body": draft_body,
            "template_used": "fallback_enhanced",
            "variables_used": {}
        }


def _enhance_draft(base_draft: str, subject: str, body: str, function: str, intent: str, action: str) -> str:
    """Enhance a draft with context-aware content"""
    # Extract key information from email
    body_lower = body.lower()
    
    # Build context-aware response
    if function == "Sales" and "pricing" in body_lower:
        return f"""Hello,

Thank you for your interest in our platform. I'd be happy to provide you with detailed pricing information for your team.

Based on your inquiry about enterprise pricing, I can prepare a customized quote that fits your needs. Would you be available for a brief call this week to discuss your specific requirements? This will help me provide you with the most accurate pricing and feature comparison.

I'll also send you our detailed feature comparison document and integration options.

Looking forward to speaking with you.

Best regards"""
    
    elif function == "Sales" and intent == "Inquiry":
        return f"""Hello,

Thank you for reaching out. I'd be happy to help answer your questions about our platform.

{_extract_key_question(body)}

Let me provide you with the information you need and suggest next steps for moving forward.

Best regards"""
    
    elif function == "Hiring" and intent == "Application":
        return f"""Hello,

Thank you for your interest in joining our team. We've received your application and our hiring team will review it carefully.

We'll be in touch within the next week if we'd like to move forward with the next steps in our process.

Best regards"""
    
    elif recommended_action == "Ask for missing information":
        return f"""Hello,

Thank you for your email. To better assist you, I need a bit more information.

Could you please provide:
- [Specific information needed based on email]

Once I have these details, I'll be able to help you more effectively.

Best regards"""
    
    elif recommended_action == "Schedule meeting":
        return f"""Hello,

Thank you for reaching out. I'd be happy to schedule a call to discuss this further.

I'm available:
- [Day] at [Time]
- [Day] at [Time]

Please let me know which time works best for you, or suggest an alternative time if these don't work.

Best regards"""
    
    else:
        # Generic but professional response
        return f"""Hello,

Thank you for your email regarding {subject.lower()}.

I've received your message and will review it carefully. I'll get back to you with a detailed response soon.

If this is urgent, please don't hesitate to reach out.

Best regards"""


def _extract_key_question(body: str) -> str:
    """Extract key question from email body"""
    # Simple extraction - look for question marks or numbered lists
    lines = body.split('\n')
    for line in lines:
        if '?' in line and len(line.strip()) > 10:
            return line.strip()
    # If no question found, return generic
    return "I'd be happy to provide you with the information you need."

