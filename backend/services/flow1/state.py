"""
Flow 1 State Definition
Defines the state structure that flows through all LangGraph nodes
"""
from typing import TypedDict, Optional, List, Dict


class Flow1State(TypedDict):
    """
    State structure for Flow 1: Inbound Email → Response
    
    Carries data through all 7 steps:
    1. Email Ingestion (input)
    2. Classification (AI)
    3. Priority Scoring (AI)
    4. Executive Summary (AI)
    5. Action Recommendation (AI)
    6. Draft Generation (AI)
    7. Review & Log (post-processing)
    """
    # Step 1: Email Ingestion (input)
    company_id: str
    email_subject: str
    email_body: str
    from_email: str
    to_email: str
    thread_id: Optional[str]
    gmail_message_id: Optional[str]
    thread_history: List[Dict]  # Previous emails in thread for context (empty list if new thread)
    thread_count: int  # Number of previous emails (0 = new thread)
    
    # Brand Context (loaded once before graph execution)
    # Structure: {"full": {...}, "key_points": {...}}
    # - full: Complete documents (company, voice, playbooks, policies, knowledge, templates)
    # - key_points: Extracted lightweight points for optimization (~200-300 tokens)
    brand_context: Optional[Dict]
    
    # Step 2: Classification (output)
    function: Optional[str]  # Sales/Hiring/Legal/Support/Ops/Marketing/Admin
    intent: Optional[str]  # Inquiry/Follow-up/Objection/Scheduling/Application/FAQ/Complaint
    urgency: Optional[str]  # Immediate/Soon/Can wait
    impact: Optional[str]  # Revenue/Hiring/Brand/Low
    confidence: Optional[str]  # Clear/Ambiguous/Missing info
    classification_metadata: Optional[dict]
    
    # Step 3: Priority Scoring (output)
    priority_score: Optional[int]  # 0-100
    
    # Step 4: Executive Summary (output)
    executive_summary: Optional[str]  # 1-2 lines, max 150 chars
    
    # Step 5: Action Recommendation (output)
    recommended_action: Optional[str]  # Reply with template/Ask for info/Schedule meeting/etc
    
    # Step 6: Draft Generation (output)
    draft_subject: Optional[str]
    draft_body: Optional[str]
    template_used: Optional[str]
    variables_used: Optional[dict]
    
    # Step 7: Review & Log (metadata)
    email_id: Optional[str]
    draft_id: Optional[str]
    status: str  # "processing", "completed", "error"
    error_message: Optional[str]

