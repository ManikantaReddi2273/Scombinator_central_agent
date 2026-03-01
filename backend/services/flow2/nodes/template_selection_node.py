"""
Template Selection Node - Step 3 of Flow 2
Selects appropriate email template based on intent and recipient context
"""
from typing import Dict, Optional
from services.flow2.state import Flow2State
import logging

logger = logging.getLogger(__name__)


async def template_selection_node(state: Flow2State) -> Dict:
    """
    Step 3: Template Selection
    
    Selects appropriate template based on:
    - Outbound intent (followup_checkin, schedule_meeting, send_proposal, address_objection)
    - Lead stage
    - Email type (B2B vs B2C)
    - Available templates in brand context
    
    Args:
        state: Flow2State with outbound_intent, recipient_context, brand_context
        
    Returns:
        Dict with selected_template_key, template_content, required_variables
    """
    outbound_intent = state.get("outbound_intent", "followup_checkin")
    recipient_context = state.get("recipient_context", {})
    brand_context = state.get("brand_context")
    email_type = state.get("email_type", "B2B")
    
    # Get templates from brand context (loaded from Redis cache via orchestrator)
    templates = {}
    if brand_context and isinstance(brand_context, dict):
        full_context = brand_context.get("full", {})
        if isinstance(full_context, dict):
            templates = full_context.get("templates", {})
            logger.info(f"Using brand context templates: {len(templates)} templates available")
    else:
        logger.warning("Brand context not available in state - template selection without brand templates")
    
    # Get lead stage for template matching
    lead_stage = recipient_context.get("lead_stage", "")
    lead_stage_lower = lead_stage.lower() if lead_stage else ""
    
    # Map intent to template patterns
    template_patterns = {
        "initial_outreach": [
            "outreach/initial_outreach.md",
            "outreach/b2c_initial.md",
            "initial_outreach.md",
            "b2c_initial.md"
        ],
        "followup_checkin": [
            "outreach/soft_follow_up.md",
            "outreach/follow_up.md",
            "follow_up.md",
            "soft_follow_up.md"
        ],
        "schedule_meeting": [
            "outreach/schedule_meeting.md",
            "outreach/meeting_request.md",
            "schedule_meeting.md",
            "meeting_request.md"
        ],
        "send_proposal": [
            "outreach/send_proposal.md",
            "outreach/proposal.md",
            "send_proposal.md",
            "proposal.md"
        ],
        "address_objection": [
            "outreach/address_objection.md",
            "outreach/objection_response.md",
            "address_objection.md",
            "objection_response.md"
        ]
    }
    
    # Try to find matching template
    selected_template_key = None
    template_content = None
    
    # Get template patterns for this intent
    patterns = template_patterns.get(outbound_intent, [])
    
    # Try each pattern
    for pattern in patterns:
        # Try exact match first
        if pattern in templates:
            selected_template_key = pattern
            template_content = templates[pattern]
            logger.info(f"Found template: {pattern}")
            break
        
        # Try case-insensitive match
        for key in templates.keys():
            if key.lower() == pattern.lower():
                selected_template_key = key
                template_content = templates[key]
                logger.info(f"Found template (case-insensitive): {key}")
                break
        
        if selected_template_key:
            break
    
    # If no specific template found, try generic outreach templates
    if not selected_template_key:
        for key in templates.keys():
            if "outreach" in key.lower() or "follow" in key.lower():
                selected_template_key = key
                template_content = templates[key]
                logger.info(f"Using generic outreach template: {key}")
                break
    
    # If still no template, use first available template
    if not selected_template_key and templates:
        selected_template_key = list(templates.keys())[0]
        template_content = templates[selected_template_key]
        logger.info(f"Using first available template: {selected_template_key}")
    
    # If no templates available, set to None (draft generator will handle it)
    if not selected_template_key:
        logger.warning("No templates found in brand context, draft generator will create from scratch")
        selected_template_key = None
        template_content = None
    
    # Identify required variables from template
    required_variables = {}
    if template_content:
        # Extract variables from template (simple pattern matching)
        import re
        # Find {variable} patterns
        variables = re.findall(r'\{(\w+)\}', template_content)
        for var in variables:
            # Map common variable names to recipient context fields
            var_lower = var.lower()
            if "name" in var_lower or "contact" in var_lower:
                required_variables[var] = recipient_context.get("name", "")
            elif "company" in var_lower or "institution" in var_lower:
                required_variables[var] = recipient_context.get("company", "")
            elif "role" in var_lower:
                required_variables[var] = recipient_context.get("role", "")
            elif "stage" in var_lower:
                required_variables[var] = recipient_context.get("lead_stage", "")
            elif "activity" in var_lower or "last" in var_lower:
                last_activity = recipient_context.get("last_activity", {})
                if last_activity:
                    required_variables[var] = last_activity.get("summary", "")
                else:
                    required_variables[var] = ""
            elif "days" in var_lower:
                days = recipient_context.get("days_since_activity")
                required_variables[var] = str(days) if days is not None else "0"
            else:
                # Default to empty string
                required_variables[var] = recipient_context.get(var, "")
    
    logger.info(f"Template selected: {selected_template_key}, variables: {list(required_variables.keys())}")
    
    return {
        "selected_template_key": selected_template_key,
        "template_content": template_content,
        "required_variables": required_variables
    }

