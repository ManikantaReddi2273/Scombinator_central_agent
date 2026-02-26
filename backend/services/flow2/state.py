"""
Flow 2 State Definition
Defines the state structure that flows through all LangGraph nodes
"""
from typing import TypedDict, Optional, List, Dict


class Flow2State(TypedDict):
    """
    State structure for Flow 2: Outbound Email → Send
    
    Carries data through all 6 steps:
    1. Intent Definition (input)
    2. Recipient Context Gathering (input)
    3. Template Selection (AI)
    4. Draft Generation (AI)
    5. Review & Scheduling (post-processing)
    6. Tracking & Feedback Loop (post-processing)
    """
    # Step 1: Intent Definition (input)
    company_id: str
    lead_id: str  # From CRM
    lead_data: Dict  # Full lead record from LEADS.xlsx
    activities: List[Dict]  # Previous activities from ACTIVITIES.xlsx
    email_type: str  # "B2B" or "B2C"
    trigger_type: str  # manual, time_based, calendar, task
    user_intent: Optional[str]  # Intent provided by user (if manual trigger)
    thread_id: Optional[str]  # For follow-ups: same thread as first outbound (so Gmail threads correctly)
    
    # Brand Context (loaded once before graph execution)
    brand_context: Optional[Dict]
    
    # Step 2: Intent Definition (output)
    outbound_intent: Optional[str]  # followup_checkin, schedule_meeting, send_proposal, address_objection
    
    # Step 3: Recipient Context (output)
    recipient_context: Optional[Dict]  # Enriched recipient data with name, company, role, stage, engagement, previous interactions
    
    # Step 4: Template Selection (output)
    selected_template_key: Optional[str]  # Template path from brand context (e.g., "outreach/soft_follow_up.md")
    template_content: Optional[str]  # Template content
    required_variables: Optional[Dict]  # Variables to fill in template
    
    # Step 5: Draft Generation (output)
    draft_subject: Optional[str]
    draft_body: Optional[str]
    
    # Status
    status: str  # "processing", "completed", "error"
    
    # Error handling
    error: Optional[str]  # Error message if processing fails

