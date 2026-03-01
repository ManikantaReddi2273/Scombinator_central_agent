"""
Draft Generator Node - Step 4 of Flow 2
Generates outbound email draft using template and brand context
"""
from typing import Dict
from services.flow2.state import Flow2State
from services.openai_client import openai_client
import logging
import re

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
    ]
    
    lines = body.split('\n')
    cleaned_lines = []
    skip_until_blank = False
    
    for line in lines:
        line_lower = line.lower().strip()
        
        if any(pattern.lower() in line_lower for pattern in instruction_patterns):
            skip_until_blank = True
            continue
        
        if skip_until_blank and not line.strip():
            skip_until_blank = False
            continue
        
        if not skip_until_blank:
            cleaned_line = line.replace("**", "").replace("*", "").replace("---", "")
            cleaned_lines.append(cleaned_line)
    
    body = '\n'.join(cleaned_lines)
    
    # Remove placeholders
    body = body.replace("[Your Name]", "")
    body = body.replace("[Your Company Name]", "")
    
    # Clean up multiple blank lines
    while "\n\n\n" in body:
        body = body.replace("\n\n\n", "\n\n")
    
    return body.strip()


async def draft_generator_node(state: Flow2State) -> Dict:
    """
    Step 4: Draft Generation
    
    Generates outbound email draft using:
    - Selected template (if available)
    - Brand context (voice, tone, policies)
    - Recipient context (personalization)
    - Required variables
    
    Args:
        state: Flow2State with template_content, recipient_context, brand_context
        
    Returns:
        Dict with draft_subject and draft_body
    """
    company_id = state.get("company_id")
    outbound_intent = state.get("outbound_intent", "followup_checkin")
    recipient_context = state.get("recipient_context", {})
    template_content = state.get("template_content")
    required_variables = state.get("required_variables", {})
    brand_context = state.get("brand_context")
    email_type = (state.get("email_type") or "B2B").strip().lower()
    is_b2c = email_type == "b2c"
    
    # Get brand context components (loaded from Redis cache via orchestrator)
    # Brand context structure: {"full": {...}, "key_points": {...}}
    # - full: Complete documents from Drive (company, voice, playbooks, policies, knowledge, templates)
    brand_tone = None
    company_info = None
    policies = None
    playbooks = None
    
    if brand_context and isinstance(brand_context, dict):
        full_context = brand_context.get("full", {})
        if isinstance(full_context, dict):
            voice_content = full_context.get("voice", "")
            company_info = full_context.get("company", "")
            policies = full_context.get("policies", "")
            playbooks = full_context.get("playbooks", "")
            
            if voice_content:
                brand_tone = voice_content
            
            logger.info(f"Using brand context: voice={'yes' if brand_tone else 'no'}, company_info={'yes' if company_info else 'no'}, policies={'yes' if policies else 'no'}")
    else:
        logger.warning("Brand context not available in state - draft generation may not match brand voice")
    
    # Extract recipient information
    recipient_name = recipient_context.get("name", "")
    recipient_company = recipient_context.get("company", "")
    recipient_role = recipient_context.get("role", "")
    lead_stage = recipient_context.get("lead_stage", "")
    engagement_level = recipient_context.get("engagement_level", "")
    last_activity = recipient_context.get("last_activity", {})
    days_since_activity = recipient_context.get("days_since_activity")
    objection_notes = recipient_context.get("objection_notes", "")
    notes = recipient_context.get("notes", "")
    campaign = recipient_context.get("campaign", "")
    campaign_id = recipient_context.get("campaign_id", "")
    source = recipient_context.get("source", "")
    
    # Build last activity context
    last_activity_text = ""
    if last_activity:
        activity_type = last_activity.get("type", "")
        activity_summary = last_activity.get("summary", "")
        if activity_summary:
            last_activity_text = f"Last interaction: {activity_summary}"
            if days_since_activity is not None:
                last_activity_text += f" ({days_since_activity} days ago)"
    
    # Build template context
    template_context = ""
    if template_content:
        # Fill in variables
        filled_template = template_content
        for var, value in required_variables.items():
            filled_template = filled_template.replace(f"{{{var}}}", str(value))
        
        template_context = f"\n\nUSE THIS TEMPLATE AS YOUR PRIMARY GUIDE:\n{filled_template}"
    else:
        template_context = "\n\nNo specific template available - create a professional outbound email."
    
    # Build brand tone context
    tone_context = f"\n\nBRAND VOICE AND TONE (CRITICAL - FOLLOW THESE RULES EXACTLY):\n{brand_tone}" if brand_tone else ""
    
    # Build intent-specific guidance
    intent_guidance = ""
    if is_b2c and outbound_intent == "initial_outreach":
        intent_guidance = """
INTENT: B2C Initial Outreach (post-context)
- This person commented on a social post (e.g. LinkedIn/Instagram) with their name and email
- Reference the SPECIFIC post/campaign they commented on (use Campaign and Notes below)
- Thank them for their interest; keep it warm and relevant to that post
- Invite them to take the next step (e.g. try the product, get more info)
- Follow brand voice; keep it concise and human"""
    elif is_b2c and outbound_intent == "followup_checkin":
        intent_guidance = """
INTENT: B2C Follow-up
- They haven't replied to our first (or previous) email about the post/campaign
- Gently reference the post/campaign again; one new angle or reminder
- Keep tone from brand context; follow-up format from playbooks
- Short and friendly"""
    elif outbound_intent == "followup_checkin":
        intent_guidance = """
INTENT: Follow-up Check-in
- Check in on previous interaction
- Reference last activity naturally
- Ask if they have questions
- Suggest next steps
- Keep it brief and friendly"""
    
    elif outbound_intent == "schedule_meeting":
        intent_guidance = """
INTENT: Schedule Meeting
- Get to the point quickly
- Suggest 2-3 specific time slots
- Make it easy to pick a time
- Keep it short (2-3 paragraphs max)"""
    
    elif outbound_intent == "send_proposal":
        intent_guidance = """
INTENT: Send Proposal
- Reference previous discussions
- Mention proposal is attached/ready
- Highlight key points
- Suggest next steps
- Professional but friendly"""
    
    elif outbound_intent == "address_objection":
        intent_guidance = """
INTENT: Address Objection
- Acknowledge their concern
- Address it directly and honestly
- Provide value/alternative perspective
- Don't be pushy
- Suggest next steps if appropriate"""
    
    # B2C post context (the post/campaign they commented on)
    b2c_post_context = ""
    if is_b2c and (campaign or notes):
        b2c_post_context = f"""
POST/CAMPAIGN THEY COMMENTED ON (reference this in the email):
- Campaign: {campaign or "(see notes)"}
- Campaign ID: {campaign_id or ""}
- Notes: {notes or ""}
- Source: {source or ""}
"""
    
    # Enhanced prompt with few-shot examples for outbound emails
    channel_label = "B2C (social post follow-up)" if is_b2c else "B2B"
    prompt = f"""You are a professional email writer for outbound {channel_label} communications. Write a COMPLETE, DETAILED outbound email that is personalized, professional, and effective.

RECIPIENT INFORMATION:
- Name: {recipient_name}
- Company: {recipient_company}
- Role: {recipient_role}
- Lead Stage: {lead_stage}
- Engagement Level: {engagement_level}
{b2c_post_context}
{last_activity_text}
{objection_notes if objection_notes else ""}
{notes if notes else ""}

{company_info if company_info else ""}
{tone_context}
{template_context}
{intent_guidance}

REQUIREMENTS:
1. Personalize using recipient's name and company
2. Reference last activity or previous interactions if relevant
3. Follow brand voice rules exactly
4. Include concrete next steps or time slots for meetings
5. Keep it concise (2-4 paragraphs)
6. Professional but friendly tone

BRAND VOICE RULES (MUST FOLLOW):
- Get to the point quickly
- Use "you" and "your" - make it about them
- Use contractions: "We're", "you'll", "I'd"
- Short paragraphs (2-3 sentences max)
- End with clear next step
- NEVER use "Best regards" - use "Best," instead
- NEVER use corporate jargon
- Sound like a human wrote it

FEW-SHOT EXAMPLES:

Example 1 - Follow-up Check-in:
Input:
Name: Sarah Johnson
Company: TechCorp
Last Activity: "Sent pricing information 3 days ago"
Output:
Hi Sarah,

I wanted to follow up on the pricing information I sent earlier this week. Do you have any questions about the proposal or would you like to discuss next steps?

I'm happy to schedule a quick call to walk through how this would work for TechCorp.

Best,

Example 2 - Schedule Meeting:
Input:
Name: Michael Chen
Company: DataFlow Inc
Lead Stage: "Qualified"
Output:
Hi Michael,

I'd love to show you how our platform can help DataFlow Inc streamline your operations. Based on what you mentioned, I think it could be a great fit.

Here are a few times that work for me next week:
- Tuesday at 2 PM IST
- Wednesday at 10 AM IST
- Thursday at 4 PM IST

Which works best for you?

Best,

Example 3 - Send Proposal:
Input:
Name: Emily Rodriguez
Company: CloudSolutions
Last Activity: "Discussed requirements 5 days ago"
Output:
Hi Emily,

Following up on our conversation last week — I've prepared a proposal tailored to CloudSolutions' needs. It includes the pricing and implementation timeline we discussed.

I've attached it here. Let me know if you have any questions or if you'd like to schedule a call to review it together.

Best,

Example 4 - Address Objection:
Input:
Name: David Kim
Company: Enterprise Systems
Objection Notes: "Concerned about implementation time"
Output:
Hi David,

I understand your concern about implementation time. Many of our customers had the same worry, but most are up and running within 2 weeks.

I'd be happy to walk you through our implementation process and show you how we make it quick and smooth. Can we schedule a 15-minute call this week?

Best,

NOW WRITE THE OUTBOUND EMAIL:
Based on the recipient information above, write a COMPLETE outbound email that:
- Personalizes using name and company
- References context if available
- Follows brand voice rules exactly
- Includes clear next steps
- For scheduling: MUST include 2-3 specific time slots
- Length: 2-4 paragraphs

Return ONLY the email body text, nothing else:"""

    messages = [
        {
            "role": "system",
            "content": "You are a professional email writer. Return ONLY the email body text - plain text, no markdown, no explanations, no instructions, no notes, no code blocks. Just the email content that can be sent directly."
        },
        {
            "role": "user",
            "content": prompt
        }
    ]
    
    try:
        response = await openai_client.chat_completion(
            messages=messages,
            temperature=0.8,
            max_tokens=800
        )
        
        draft_body = response.strip()
        draft_body = _clean_draft_body(draft_body)
        
        # Generate subject line
        subject_prefix = "Re: " if last_activity and last_activity.get("subject") else ""
        
        if is_b2c and outbound_intent == "initial_outreach":
            draft_subject = f"Thanks for your interest – {campaign or 'following up'}"
        elif is_b2c and outbound_intent == "followup_checkin":
            draft_subject = f"{subject_prefix}Quick follow-up – {campaign or 'your interest'}"
        elif outbound_intent == "followup_checkin":
            draft_subject = f"{subject_prefix}Following up on {recipient_company}"
        elif outbound_intent == "schedule_meeting":
            draft_subject = f"Quick call to discuss {recipient_company}'s needs"
        elif outbound_intent == "send_proposal":
            draft_subject = f"Proposal for {recipient_company}"
        elif outbound_intent == "address_objection":
            draft_subject = f"Re: {recipient_company} - Let's discuss"
        else:
            draft_subject = f"Re: {recipient_company}"
        
        logger.info(f"Draft generated successfully: {len(draft_body)} characters, intent={outbound_intent}")
        
        return {
            "draft_subject": draft_subject,
            "draft_body": draft_body
        }
        
    except Exception as e:
        logger.error(f"Draft generation error: {str(e)}", exc_info=True)
        # Fallback draft
        fallback_body = f"""Hi {recipient_name},

I wanted to follow up on our previous conversation about {recipient_company}.

{last_activity_text if last_activity_text else "I'd like to continue the discussion and see how we can help."}

Would you be available for a quick call this week to discuss next steps?

Best,"""
        
        return {
            "draft_subject": f"Re: {recipient_company}",
            "draft_body": fallback_body
        }

