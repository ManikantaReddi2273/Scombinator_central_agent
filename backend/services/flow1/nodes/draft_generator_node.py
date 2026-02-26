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
    
    # Get brand context from state (loaded from Redis cache via orchestrator)
    # Brand context structure: {"full": {...}, "key_points": {...}}
    # - full: Complete documents from Drive (company, voice, playbooks, policies, knowledge, templates)
    # - key_points: Extracted lightweight points for optimization
    templates = {}
    brand_tone = None
    knowledge = None
    company_info = None
    policies = None
    playbooks = None
    
    brand_context = state.get("brand_context")
    if brand_context and isinstance(brand_context, dict):
        full_context = brand_context.get("full", {})
        if isinstance(full_context, dict):
            # Get full documents from brand context (loaded from Drive, cached in Redis)
            templates = full_context.get("templates", {})
            voice_content = full_context.get("voice", "")
            knowledge = full_context.get("knowledge", "")
            company_info = full_context.get("company", "")
            policies = full_context.get("policies", "")
            playbooks = full_context.get("playbooks", "")
            
            # Use full voice content (not truncated) - it's critical for brand consistency
            if voice_content:
                brand_tone = voice_content  # Use full document for better context
            
            logger.info(f"Using brand context: {len(templates)} templates, voice={'yes' if brand_tone else 'no'}, policies={'yes' if policies else 'no'}")
    else:
        logger.warning("Brand context not available in state - draft generation may not match brand voice")
    
    # Fallback: Try old policy_loader_service if brand context not available (should not happen in normal flow)
    if not templates and not brand_tone:
        # Extract db from config if available
        db = None
        if config and isinstance(config, dict):
            db = config.get("db")
        
        if db and company_id:
            try:
                from services.policy_loader import policy_loader_service
                templates = await policy_loader_service.get_templates(db, company_id)
                brand_tone = await policy_loader_service.get_brand_tone(db, company_id)
            except Exception as e:
                logger.warning(f"Error loading company templates for {company_id}: {str(e)}")
                # Continue with defaults
    
    # Check for specific template match first (e.g., pricing_inquiry.md, demo requests)
    matched_template = None
    template_key = None
    
    # For pricing inquiries, use the pricing_inquiry template
    if function == "Sales" and ("pricing" in email_body.lower() or "price" in email_body.lower() or "cost" in email_body.lower()):
        # Look for pricing_inquiry template
        for key in templates.keys():
            if "pricing" in key.lower() or "price" in key.lower():
                matched_template = templates[key]
                template_key = key
                logger.info(f"Using matched template: {key}")
                break
    
    # For demo/scheduling requests, look for demo-related templates
    elif recommended_action == "Schedule meeting" or ("demo" in email_body.lower() or "schedule" in email_body.lower()):
        # Look for demo-related templates
        for key in templates.keys():
            if "demo" in key.lower() or "schedule" in key.lower() or "meeting" in key.lower():
                matched_template = templates[key]
                template_key = key
                logger.info(f"Using matched template: {key}")
                break
    
    # Build context from templates if available
    template_context = ""
    if matched_template:
        # Use the matched template as primary guidance
        template_context = f"\n\nUSE THIS TEMPLATE AS YOUR PRIMARY GUIDE (follow its structure and tone):\n{matched_template}"
    elif templates:
        template_names = list(templates.keys())[:5]  # Limit to first 5 for context
        template_context = f"\n\nAvailable company templates for reference: {', '.join(template_names)}"
        # Include a sample template if available
        if templates:
            first_template_key = list(templates.keys())[0]
            sample_template = templates[first_template_key][:500] if templates[first_template_key] else ""  # First 500 chars
            if sample_template:
                template_context += f"\n\nSample template structure:\n{sample_template}"
    
    # Brand voice context (full document)
    tone_context = f"\n\nBRAND VOICE AND TONE (CRITICAL - FOLLOW THESE RULES EXACTLY):\n{brand_tone}" if brand_tone else ""
    
    # Add knowledge/FAQs context if available
    knowledge_context = ""
    if knowledge:
        # Use first 800 chars of knowledge for FAQ context
        knowledge_preview = knowledge[:800]
        knowledge_context = f"\n\nCompany Knowledge Base (FAQs and approved answers):\n{knowledge_preview}"
    
    # Add policies context (especially pricing policy)
    policies_context = ""
    if policies:
        # Extract pricing policy section if available
        if "pricing" in policies.lower() or "price" in policies.lower():
            # Find pricing section
            policies_lower = policies.lower()
            pricing_start = policies_lower.find("pricing")
            if pricing_start != -1:
                pricing_section = policies[max(0, pricing_start-100):pricing_start+1000]
                policies_context = f"\n\nCRITICAL POLICY (MUST FOLLOW):\n{pricing_section}"
            else:
                policies_context = f"\n\nCompany Policies (first 800 chars):\n{policies[:800]}"
        else:
            policies_context = f"\n\nCompany Policies (first 800 chars):\n{policies[:800]}"
    
    # Add company info context
    company_context = ""
    if company_info:
        # Extract key company details (first 600 chars)
        company_preview = company_info[:600]
        company_context = f"\n\nCompany Information:\n{company_preview}"
    
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
ACTION TYPE: Schedule Meeting (CRITICAL - MUST INCLUDE SPECIFIC TIMES)
- Get to the point quickly: "Happy to schedule a demo"
- Answer their questions briefly (1-2 sentences each)
- MUST suggest 2-3 SPECIFIC time slots (e.g., "Tuesday at 2 PM IST", "Wednesday at 10 AM IST", "Thursday at 4 PM IST")
- Keep it short and direct (2-3 paragraphs max)
- Make it easy for them to pick a time
- Example structure:
  "Hi [Name],
  
  Happy to schedule a demo! I can show you how Resolvely works and answer your questions about onboarding, integrations, and training.
  
  Here are a few times that work for me next week:
  - Tuesday, [date] at 2 PM IST
  - Wednesday, [date] at 10 AM IST  
  - Thursday, [date] at 4 PM IST
  
  Which works best for you? Or suggest another time if these don't work.
  
  Best,"""
    elif function == "Sales" and ("pricing" in email_body.lower() or "price" in email_body.lower()):
        action_guidance = """
ACTION TYPE: Pricing Inquiry (CRITICAL POLICY)
- NEVER discuss specific pricing, tiers, or packages in email
- ALWAYS route to a call: "Pricing depends on your specific setup and volume — I want to make sure I give you accurate numbers rather than a generic range. Can we do a quick 15-min call to go through it?"
- Keep it friendly, not evasive
- Make the call sound quick and valuable (not a sales pitch)
- Use the pricing_inquiry template if available"""
    else:  # Reply with template
        action_guidance = """
ACTION TYPE: Standard Response
- Address their inquiry directly
- Provide helpful information
- Include next steps or call-to-action
- Be professional and friendly"""
    
    # Enhanced prompt with few-shot examples aligned with brand voice
    prompt = f"""You are a professional email writer for {company_info.splitlines()[0].replace('**Company Name** |', '').strip() if company_info else 'a company'}. Write a COMPLETE, DETAILED email response that directly addresses the sender's inquiry.

ORIGINAL EMAIL RECEIVED:
Subject: {email_subject}
From: {from_email}
Body: {body_truncated}
{thread_context}

EMAIL CONTEXT:
- Business Function: {function}
- Email Intent: {intent}
- Recommended Action: {recommended_action}
{company_context}
{tone_context}
{template_context}
{knowledge_context}
{policies_context}
{action_guidance}

REQUIREMENTS:
1. Address their specific question/request directly
2. Follow brand voice rules exactly (see above)
3. Follow policies exactly (especially pricing)
4. Use template if provided
5. Be specific and helpful
6. Include clear next steps
7. 2-4 paragraphs (shorter is better)

BRAND VOICE RULES (MUST FOLLOW):
- Get to the point quickly
- Use "you" and "your" - make it about them
- Use contractions: "We're", "you'll", "I'd"
- Short paragraphs (2-3 sentences max)
- End with clear next step
- NEVER use "Best regards" - use "Best," instead
- NEVER use "I hope this email finds you well"
- NEVER use corporate jargon
- Sound like a human wrote it

FEW-SHOT EXAMPLES:

Example 1 - Sales Pricing Inquiry:
Input:
Subject: "Enterprise Pricing Inquiry"
Body: "Hi, I'm reaching out on behalf of TechCorp. We're interested in your platform for 50+ employees. Could you provide pricing details?"
Output:
Hi Sarah,

Great question! Pricing depends on your setup — ticket volume, integrations, how you want to use it.

Rather than give you a generic number, I'd prefer to understand your situation and give you accurate pricing. It's a quick 15-minute call.

What works this week?

Best,

Example 2 - Demo/Scheduling Request:
Input:
Subject: "Product Demo Request"
Body: "I'd like to schedule a demo to see how your platform works. I have questions about onboarding and integrations."
Output:
Hi Michael,

Happy to schedule a demo! I can show you how Resolvely works and answer your questions about onboarding, integrations, and training.

Here are a few times that work for me next week:
- Tuesday at 2 PM IST
- Wednesday at 10 AM IST
- Thursday at 4 PM IST

Which works best for you? Or suggest another time if these don't work.

Best,

Example 3 - Support Inquiry:
Input:
Subject: "Question about API integration"
Body: "How do I integrate your API with our existing system? Do you have documentation?"
Output:
Hi there,

Yes, we have comprehensive API documentation. You can find it at [link] or I can send you a quick guide.

The integration is straightforward — most customers get it set up in about an hour. If you run into any issues, just reply to this email and I'll help.

Best,

Example 4 - Hiring Application:
Input:
Subject: "Application for Senior Developer"
Body: "I've attached my resume for the position. I have 8 years of experience."
Output:
Hi [Name],

Thanks for your interest in joining our team. We've received your application and our hiring team will review it carefully.

We'll be in touch within the next week if we'd like to move forward with next steps.

Best,

Example 5 - Follow-up Email:
Input:
Subject: "Re: Product Demo"
Body: "Just following up on my email from last week about scheduling a demo. Any update?"
Output:
Hi Michael,

Thanks for following up! I'd be happy to schedule that demo.

Here are a few times that work for me this week:
- Tuesday at 2 PM IST
- Wednesday at 10 AM IST
- Thursday at 4 PM IST

Which works best for you?

Best,

NOW WRITE THE EMAIL RESPONSE:
Based on the original email above, write a COMPLETE response that:
- Directly answers their specific question/request
- Provides helpful, actionable information
- Includes clear next steps
- For scheduling: MUST include 2-3 specific time slots
- Length: 2-4 paragraphs
- Follows brand voice rules exactly

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
        
        # Apply brand tone adjustments and enforce brand voice rules
        if brand_tone:
            # Enforce brand voice rules - remove forbidden phrases
            draft_body = draft_body.replace("Best regards", "Best,")
            draft_body = draft_body.replace("Warm regards", "Best,")
            draft_body = draft_body.replace("Kind regards", "Best,")
            draft_body = draft_body.replace("Thanks and regards", "Thanks,")
            draft_body = draft_body.replace("I hope this email finds you well", "")
            draft_body = draft_body.replace("please do not hesitate to contact", "reply to this email")
            draft_body = draft_body.replace("Please do not hesitate to contact", "Reply to this email")
            
            # Remove corporate jargon
            draft_body = draft_body.replace("leverage", "use")
            draft_body = draft_body.replace("Leverage", "Use")
            draft_body = draft_body.replace("utilize", "use")
            draft_body = draft_body.replace("Utilize", "Use")
            draft_body = draft_body.replace("facilitate", "help")
            draft_body = draft_body.replace("Facilitate", "Help")
            draft_body = draft_body.replace("circle back", "follow up")
            draft_body = draft_body.replace("Circle back", "Follow up")
            draft_body = draft_body.replace("touch base", "connect")
            draft_body = draft_body.replace("Touch base", "Connect")
            
            # Ensure contractions are used
            draft_body = draft_body.replace("We are", "We're")
            draft_body = draft_body.replace("we are", "we're")
            draft_body = draft_body.replace("You will", "You'll")
            draft_body = draft_body.replace("you will", "you'll")
            draft_body = draft_body.replace("I would", "I'd")
            draft_body = draft_body.replace("i would", "I'd")
            
            tone_lower = brand_tone.lower()
            if "short" in tone_lower or "brief" in tone_lower:
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
    """Enhance a draft with context-aware content following brand voice"""
    # Extract key information from email
    body_lower = body.lower()
    
    # Extract name from email if possible
    name = "there"
    if "regards" in body_lower or "best" in body_lower:
        # Try to extract name from signature
        lines = body.split('\n')
        for line in lines[-5:]:  # Check last 5 lines
            if len(line.strip()) > 0 and len(line.strip()) < 50:
                name = line.strip().split()[0] if line.strip().split() else "there"
                break
    
    # Build context-aware response following brand voice
    if function == "Sales" and ("pricing" in body_lower or "price" in body_lower):
        return f"""Hi {name},

Great question! Pricing depends on your setup — ticket volume, integrations, how you want to use it.

Rather than give you a generic number, I'd prefer to understand your situation and give you accurate pricing. It's a quick 15-minute call.

What works this week?

Best,"""
    
    elif function == "Sales" and intent == "Inquiry":
        return f"""Hi {name},

Thanks for reaching out. I'd be happy to help answer your questions about our platform.

{_extract_key_question(body)}

Let me provide you with the information you need and suggest next steps.

Best,"""
    
    elif function == "Hiring" and intent == "Application":
        return f"""Hi {name},

Thanks for your interest in joining our team. We've received your application and our hiring team will review it carefully.

We'll be in touch within the next week if we'd like to move forward with next steps.

Best,"""
    
    elif action == "Ask for missing information":
        return f"""Hi {name},

Thanks for your email. To better assist you, I need a bit more information.

Could you please provide:
- [Specific information needed based on email]

Once I have these details, I'll be able to help you more effectively.

Best,"""
    
    elif action == "Schedule meeting":
        # Extract demo-related questions from body
        demo_questions = []
        body_lower = body.lower()
        if "onboarding" in body_lower or "onboard" in body_lower:
            demo_questions.append("onboarding")
        if "integration" in body_lower or "integrate" in body_lower:
            demo_questions.append("integrations")
        if "training" in body_lower or "support" in body_lower:
            demo_questions.append("training and support")
        
        questions_text = ""
        if demo_questions:
            questions_text = f" I can show you how Resolvely works and answer your questions about {', '.join(demo_questions)}."
        
        return f"""Hi {name},

Happy to schedule a demo!{questions_text}

Here are a few times that work for me next week:
- Tuesday at 2 PM IST
- Wednesday at 10 AM IST
- Thursday at 4 PM IST

Which works best for you? Or suggest another time if these don't work.

Best,"""
    
    else:
        # Generic but professional response following brand voice
        return f"""Hi {name},

Thanks for your email regarding {subject.lower()}.

I've received your message and will review it carefully. I'll get back to you with a detailed response soon.

If this is urgent, reply to this email and I'll prioritize it.

Best,"""


def _extract_key_question(body: str) -> str:
    """Extract key question from email body"""
    # Simple extraction - look for question marks or numbered lists
    lines = body.split('\n')
    for line in lines:
        if '?' in line and len(line.strip()) > 10:
            return line.strip()
    # If no question found, return generic
    return "I'd be happy to provide you with the information you need."

