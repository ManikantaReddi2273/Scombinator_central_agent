"""
Recipient Context Node - Step 2 of Flow 2
Enriches recipient context with lead data and activity history
"""
from typing import Dict
from services.flow2.state import Flow2State
from datetime import datetime
import logging

logger = logging.getLogger(__name__)


async def recipient_context_node(state: Flow2State) -> Dict:
    """
    Step 2: Recipient Context Gathering
    
    Enriches recipient context with:
    - Lead data (name, company, role, stage, engagement)
    - Previous interactions
    - Relationship context
    - Personalization data
    
    Args:
        state: Flow2State with lead_data and activities
        
    Returns:
        Dict with recipient_context
    """
    lead_data = state.get("lead_data", {})
    activities = state.get("activities", [])
    
    # Extract key lead information
    contact_name = lead_data.get("Contact_Name", "")
    institution_name = lead_data.get("Institution_Name", "")
    role = lead_data.get("Role", "")
    email = lead_data.get("Email", "")
    phone = lead_data.get("Phone", "")
    city = lead_data.get("City", "")
    source = lead_data.get("Source", "")
    segment = lead_data.get("Segment", "")
    stage = lead_data.get("Stage", "")
    engagement_level = lead_data.get("Engagement_Level", "")
    proposal_value = lead_data.get("Proposal_Value", "")
    objection_notes = lead_data.get("Objection_Notes", "")
    notes = lead_data.get("Notes", "")
    last_activity_date = lead_data.get("Last_Activity_Date", "")
    next_followup_date = lead_data.get("Next_Followup_Date", "")
    
    # Calculate days since last activity
    days_since_activity = None
    if last_activity_date:
        try:
            for fmt in ['%Y-%m-%d %H:%M:%S', '%Y-%m-%d', '%m/%d/%Y']:
                try:
                    last_date = datetime.strptime(last_activity_date, fmt)
                    days_since_activity = (datetime.now() - last_date).days
                    break
                except ValueError:
                    continue
        except Exception as e:
            logger.warning(f"Error parsing last_activity_date: {str(e)}")
    
    # Get last activity summary
    last_activity_summary = None
    if activities and len(activities) > 0:
        last_activity = activities[0]
        last_activity_summary = {
            "type": last_activity.get("Activity_Type", ""),
            "subject": last_activity.get("Subject_Title", ""),
            "summary": last_activity.get("Summary", ""),
            "date": last_activity.get("Activity_Date", ""),
            "outcome": last_activity.get("Outcome", "")
        }
    
    # Build recipient context (include lead_id for CRM update after send)
    lead_id = state.get("lead_id", "")
    recipient_context = {
        "lead_id": lead_id,
        "name": contact_name,
        "company": institution_name,
        "role": role,
        "email": email,
        "phone": phone,
        "city": city,
        "source": source,
        "segment": segment,
        "lead_stage": stage,
        "engagement_level": engagement_level,
        "proposal_value": proposal_value,
        "objection_notes": objection_notes,
        "notes": notes,
        "last_activity_date": last_activity_date,
        "next_followup_date": next_followup_date,
        "days_since_activity": days_since_activity,
        "last_activity": last_activity_summary,
        "previous_interactions": activities[:5] if activities else []  # Last 5 activities
    }
    
    logger.info(f"Recipient context built for {contact_name} ({institution_name})")
    
    return {
        "recipient_context": recipient_context
    }

