"""
Intent Definition Node - Step 1 of Flow 2
Determines outbound email intent based on trigger type and lead context
"""
from typing import Dict
from services.flow2.state import Flow2State
from datetime import datetime
import logging

logger = logging.getLogger(__name__)


async def intent_definition_node(state: Flow2State) -> Dict:
    """
    Step 1: Intent Definition
    
    Determines the outbound email intent based on:
    - Trigger type (manual, time_based, calendar, task)
    - Lead stage and context
    - User-provided intent (if manual trigger)
    - Last activity and timing
    
    Args:
        state: Flow2State with lead_data, activities, trigger_type, user_intent
        
    Returns:
        Dict with outbound_intent and email_type
    """
    trigger_type = state.get("trigger_type", "manual")
    user_intent = state.get("user_intent")
    lead_data = state.get("lead_data", {})
    activities = state.get("activities", [])
    email_type = state.get("email_type", "B2B")
    
    # If user provided intent (manual trigger), use it
    if trigger_type == "manual" and user_intent:
        intent_map = {
            "followup_checkin": "followup_checkin",
            "schedule_meeting": "schedule_meeting",
            "send_proposal": "send_proposal",
            "address_objection": "address_objection",
            "followup": "followup_checkin",
            "meeting": "schedule_meeting",
            "proposal": "send_proposal",
            "objection": "address_objection"
        }
        
        # Normalize user intent
        user_intent_lower = user_intent.lower().replace(" ", "_")
        outbound_intent = intent_map.get(user_intent_lower, "followup_checkin")
        
        logger.info(f"Using user-provided intent: {outbound_intent}")
        return {
            "outbound_intent": outbound_intent,
            "email_type": email_type
        }
    
    # Determine intent based on context
    lead_stage = lead_data.get("Stage", "")
    last_activity_date = lead_data.get("Last_Activity_Date", "")
    next_followup_date = lead_data.get("Next_Followup_Date", "")
    objection_notes = lead_data.get("Objection_Notes", "")
    
    # Calculate days since last activity
    days_since_activity = None
    if last_activity_date:
        try:
            # Try parsing various date formats
            for fmt in ['%Y-%m-%d %H:%M:%S', '%Y-%m-%d', '%m/%d/%Y']:
                try:
                    last_date = datetime.strptime(last_activity_date, fmt)
                    days_since_activity = (datetime.now() - last_date).days
                    break
                except ValueError:
                    continue
        except Exception as e:
            logger.warning(f"Error parsing last_activity_date: {str(e)}")
    
    # Determine intent based on stage and context
    outbound_intent = "followup_checkin"  # Default
    
    # Check for objections
    if objection_notes and objection_notes.strip():
        outbound_intent = "address_objection"
        logger.info(f"Intent determined: address_objection (objection notes present)")
    
    # Check stage progression
    elif lead_stage:
        stage_lower = lead_stage.lower()
        
        if "proposal" in stage_lower or "quote" in stage_lower:
            outbound_intent = "send_proposal"
            logger.info(f"Intent determined: send_proposal (stage: {lead_stage})")
        
        elif "meeting" in stage_lower or "demo" in stage_lower or "call" in stage_lower:
            outbound_intent = "schedule_meeting"
            logger.info(f"Intent determined: schedule_meeting (stage: {lead_stage})")
        
        elif "details sent" in stage_lower or "information" in stage_lower:
            # If details were sent recently, follow up
            if days_since_activity is not None and days_since_activity >= 3:
                outbound_intent = "followup_checkin"
                logger.info(f"Intent determined: followup_checkin (details sent {days_since_activity} days ago)")
            else:
                outbound_intent = "followup_checkin"
                logger.info(f"Intent determined: followup_checkin (stage: {lead_stage})")
        
        else:
            # Default follow-up check-in
            outbound_intent = "followup_checkin"
            logger.info(f"Intent determined: followup_checkin (default for stage: {lead_stage})")
    
    # Check trigger type
    if trigger_type == "time_based":
        # Time-based triggers are usually follow-ups
        if outbound_intent == "followup_checkin":
            logger.info("Intent confirmed: followup_checkin (time-based trigger)")
    
    elif trigger_type == "calendar":
        # Calendar triggers are usually meeting follow-ups
        outbound_intent = "schedule_meeting"
        logger.info("Intent determined: schedule_meeting (calendar trigger)")
    
    elif trigger_type == "task":
        # Task triggers depend on task type
        # Default to follow-up, but could be enhanced based on task description
        outbound_intent = "followup_checkin"
        logger.info("Intent determined: followup_checkin (task trigger)")
    
    logger.info(f"Final intent: {outbound_intent} for lead {state.get('lead_id')}")
    
    return {
        "outbound_intent": outbound_intent,
        "email_type": email_type
    }

