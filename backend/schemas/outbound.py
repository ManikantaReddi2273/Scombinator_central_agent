"""
Outbound email schemas
"""
from pydantic import BaseModel, field_validator
from typing import Optional, Dict, List
from datetime import datetime


class OutboundCreateRequest(BaseModel):
    """Request to create outbound email"""
    company_id: str
    lead_id: str
    email_type: str = "B2B"  # "B2B" or "B2C"
    intent: Optional[str] = None  # followup_checkin, schedule_meeting, send_proposal, address_objection
    trigger_type: str = "manual"  # manual, time_based, calendar, task


class B2BLeadResponse(BaseModel):
    """B2B lead response schema"""
    Lead_ID: str
    Institution_Name: Optional[str] = None
    Contact_Name: Optional[str] = None
    Role: Optional[str] = None
    Email: Optional[str] = None
    Phone: Optional[str] = None
    City: Optional[str] = None
    Source: Optional[str] = None
    Segment: Optional[str] = None
    Stage: Optional[str] = None
    Engagement_Level: Optional[str] = None
    Owner: Optional[str] = None
    Date_Met: Optional[str] = None
    Last_Activity_Date: Optional[str] = None
    Next_Followup_Date: Optional[str] = None
    Proposal_Value: Optional[str] = None
    Status: Optional[str] = None
    Follow_Up_Count: Optional[int] = None  # 0 = none, 1 = first follow-up sent, 2 = second follow-up sent
    Objection_Notes: Optional[str] = None
    Notes: Optional[str] = None
    company_id: str  # Added for UI filtering

    @field_validator("Follow_Up_Count", mode="before")
    @classmethod
    def coerce_follow_up_count(cls, v):
        if v is None or v == "":
            return None
        if isinstance(v, int):
            return v
        if isinstance(v, str):
            try:
                return int(v.strip())
            except ValueError:
                return None
        return None


class B2CLeadResponse(BaseModel):
    """B2C lead response schema (B2C_FUNNEL worksheet)"""
    B2C_Lead_ID: str
    Name: Optional[str] = None
    Email: Optional[str] = None
    Source: Optional[str] = None
    Campaign_id: Optional[str] = None
    Campaign: Optional[str] = None
    Stage: Optional[str] = None
    Last_Activity_Date: Optional[str] = None
    Next_Followup_Date: Optional[str] = None
    Status: Optional[str] = None
    Notes: Optional[str] = None
    Follow_Up_Count: Optional[int] = None
    company_id: str  # For UI filtering

    @field_validator("Follow_Up_Count", mode="before")
    @classmethod
    def coerce_follow_up_count(cls, v):
        if v is None or v == "":
            return None
        if isinstance(v, int):
            return v
        if isinstance(v, str):
            try:
                return int(v.strip())
            except ValueError:
                return None
        return None


class ActivityResponse(BaseModel):
    """Activity response schema"""
    Activity_ID: str
    Lead_ID: str
    Activity_Type: str
    Subject_Title: Optional[str] = None
    Summary: Optional[str] = None
    Activity_Date: Optional[str] = None
    Performed_By: Optional[str] = None
    Outcome: Optional[str] = None
    Next_Action: Optional[str] = None
    Followup_Date: Optional[str] = None


class OutboundCreateResponse(BaseModel):
    """Response after creating outbound email"""
    email_id: str
    draft_id: str
    status: str
    subject: str
    recipient: str
    lead_stage: Optional[str] = None


class OutboundUpdateCRMRequest(BaseModel):
    """Request to update CRM after email sent. LEADS/B2C_FUNNEL, ACTIVITIES, and TASKS updated and linked by lead_id."""
    lead_id: str
    lead_source: Optional[str] = None  # "b2b" or "b2c"; if not set, inferred from email.recipient_context
    activity_summary: Optional[str] = None
    next_followup_date: Optional[str] = None
    # Optional overrides; if not set, backend uses defaults from playbook and company
    stage: Optional[str] = None          # e.g. "Email Sent"; default "Email Sent"
    engagement_level: Optional[str] = None  # High, Medium, Low; default "Medium"
    owner: Optional[str] = None         # Company name; default from company record
    status: Optional[str] = None       # e.g. "Active"; default "Active"
    objection_notes: Optional[str] = None
    notes: Optional[str] = None

