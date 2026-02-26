"""
Outbound email routes
"""
from typing import List, Optional
from fastapi import APIRouter, Depends, HTTPException, status, Query
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from database import get_db
from models.admin import Admin
from models.company import Company
from models.draft import Draft
from models.email import Email
from schemas.outbound import (
    OutboundCreateRequest,
    OutboundCreateResponse,
    B2BLeadResponse,
    ActivityResponse,
    OutboundUpdateCRMRequest
)
from services.tenant import tenant_service
from services.token_manager import token_manager_service
from services.crm_loader import crm_loader_service
from services.flow2 import Flow2Orchestrator
from services.playbook_parser import parse_followup_days_after_outreach
from services.email_thread import get_lead_id_from_thread_root
from auth.jwt import get_current_admin
from uuid import UUID
import logging
from datetime import datetime, timedelta
from googleapiclient.errors import HttpError

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/api/outbound", tags=["Outbound"])


def clean_company_id(company_id: str) -> str:
    """
    Clean and validate company_id
    
    Removes curly braces and validates UUID format
    
    Args:
        company_id: Company ID string (may have braces)
        
    Returns:
        Cleaned company_id string
        
    Raises:
        HTTPException if invalid UUID format
    """
    # Remove curly braces if present
    cleaned = company_id.strip().strip('{}')
    
    # Validate UUID format
    try:
        UUID(cleaned)
    except ValueError:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Invalid company_id format: '{company_id}'. Expected UUID format (e.g., '10e9f29f-26c0-4ce8-99ee-2caff7e1d10c')"
        )
    
    return cleaned


@router.get("/b2b/leads", response_model=List[B2BLeadResponse])
async def get_b2b_leads(
    company_id: str = Query(..., description="Company ID"),
    db: AsyncSession = Depends(get_db),
    admin: Admin = Depends(get_current_admin)
):
    """
    Get all B2B leads from CRM workbook, LEADS worksheet for a company
    
    Returns list of leads with all columns from LEADS worksheet
    """
    try:
        # Clean and validate company_id (remove braces, validate UUID)
        company_id = clean_company_id(company_id)
        
        # Validate company_id belongs to authenticated admin
        company = await tenant_service.get_company_by_id(db, company_id)
        if not company:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Company not found"
            )
        
        # Verify company has OAuth connected
        if not company.encrypted_access_token:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Company OAuth not connected. Please connect OAuth first."
            )
        
        logger.info(f"Loading B2B leads for company {company_id} ({company.name})")
        
        # Load B2B leads from CRM
        try:
            leads = await crm_loader_service.get_b2b_leads(db, company_id)
        except Exception as e:
            logger.error(f"Error in get_b2b_leads for company {company_id}: {str(e)}", exc_info=True)
            # Return detailed error message
            error_msg = str(e)
            if "not found" in error_msg.lower():
                detail = f"CRM not found: {error_msg}. Please ensure: 1) CRM folder exists in Google Drive, 2) CRM Template.xlsx (or CRM.xlsx) exists in CRM folder, 3) LEADS worksheet exists in the workbook."
            elif "worksheet" in error_msg.lower():
                detail = f"Worksheet error: {error_msg}. Please ensure LEADS worksheet exists and is named exactly 'LEADS' (case-sensitive)."
            else:
                detail = f"Error loading leads: {error_msg}. Please check server logs for details."
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail=detail
            )
        
        # Add company_id to each lead for UI filtering
        for lead in leads:
            lead["company_id"] = company_id
        
        logger.info(f"Returning {len(leads)} B2B leads for company {company_id}")
        return leads
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error loading B2B leads for company {company_id}: {str(e)}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error loading leads: {str(e)}"
        )


@router.get("/b2b/debug/crm-files")
async def debug_crm_files(
    company_id: str = Query(..., description="Company ID"),
    db: AsyncSession = Depends(get_db),
    admin: Admin = Depends(get_current_admin)
):
    """
    Debug endpoint: List all files in CRM folder to help troubleshoot
    """
    try:
        # Clean and validate company_id (remove braces, validate UUID)
        company_id = clean_company_id(company_id)
        
        company = await tenant_service.get_company_by_id(db, company_id)
        if not company:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Company not found"
            )
        
        if not company.encrypted_access_token:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Company OAuth not connected"
            )
        
        # Get CRM folder
        drive_folder_id = await crm_loader_service._get_company_drive_folder_id(db, company_id)
        
        if not drive_folder_id:
            return {
                "error": "CRM folder not found",
                "suggestions": [
                    "Ensure 'CRM' folder exists in Google Drive",
                    "Check folder name is exactly 'CRM' (case-sensitive)"
                ]
            }
        
        # List all files in CRM folder
        try:
            service = await crm_loader_service.google_api.get_drive_service(db, company_id)
            results = service.files().list(
                q=f"'{drive_folder_id}' in parents and trashed=false",
                fields="files(id, name, mimeType, modifiedTime)",
                pageSize=50
            ).execute()
            files = results.get('files', [])
            
            # Detect both Google Sheets and Excel files
            spreadsheets = [f for f in files if f['mimeType'] == 'application/vnd.google-apps.spreadsheet']
            excel_files = [f for f in files if f['mimeType'] in [
                'application/vnd.openxmlformats-officedocument.spreadsheetml.sheet',
                'application/vnd.ms-excel'
            ]]
            
            # For each Google Sheets file, list worksheets
            spreadsheet_details = []
            for spreadsheet in spreadsheets:
                try:
                    sheets_service = await crm_loader_service.google_api.get_sheets_service(db, company_id)
                    sheet_metadata = sheets_service.spreadsheets().get(spreadsheetId=spreadsheet['id']).execute()
                    worksheets = sheet_metadata.get('sheets', [])
                    worksheet_names = [ws['properties']['title'] for ws in worksheets]
                    spreadsheet_details.append({
                        "id": spreadsheet['id'],
                        "name": spreadsheet['name'],
                        "type": "Google Sheets",
                        "worksheets": worksheet_names
                    })
                except HttpError as e:
                    error_msg = str(e)
                    # Check if it's an API not enabled error
                    if "SERVICE_DISABLED" in error_msg or "has not been used" in error_msg:
                        # Extract activation URL if available
                        activation_url = None
                        if "activationUrl" in error_msg:
                            import re
                            url_match = re.search(r'https://console\.developers\.google\.com[^\s\)]+', error_msg)
                            if url_match:
                                activation_url = url_match.group(0)
                        
                        spreadsheet_details.append({
                            "id": spreadsheet['id'],
                            "name": spreadsheet['name'],
                            "type": "Google Sheets",
                            "error": "Google Sheets API is not enabled",
                            "error_details": "The Google Sheets API needs to be enabled in your Google Cloud project. See instructions below.",
                            "activation_url": activation_url or "https://console.developers.google.com/apis/api/sheets.googleapis.com/overview"
                        })
                    else:
                        spreadsheet_details.append({
                            "id": spreadsheet['id'],
                            "name": spreadsheet['name'],
                            "type": "Google Sheets",
                            "error": str(e)
                        })
                except Exception as e:
                    spreadsheet_details.append({
                        "id": spreadsheet['id'],
                        "name": spreadsheet['name'],
                        "type": "Google Sheets",
                        "error": str(e)
                    })
            
            # Add Excel files to details (they will be converted when accessed)
            for excel_file in excel_files:
                spreadsheet_details.append({
                    "id": excel_file['id'],
                    "name": excel_file['name'],
                    "type": "Excel File (will be converted to Google Sheets)",
                    "note": "This Excel file will be automatically converted to Google Sheets format when accessed"
                })
            
            return {
                "crm_folder_id": drive_folder_id,
                "total_files": len(files),
                "spreadsheets": len(spreadsheets),
                "excel_files": len(excel_files),
                "files": files,
                "spreadsheet_details": spreadsheet_details
            }
        except Exception as e:
            logger.error(f"Error listing CRM files: {str(e)}", exc_info=True)
            return {
                "error": str(e),
                "crm_folder_id": drive_folder_id
            }
            
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Debug error: {str(e)}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Debug error: {str(e)}"
        )


@router.get("/b2b/leads/{lead_id}/activities", response_model=List[ActivityResponse])
async def get_lead_activities(
    lead_id: str,
    company_id: str = Query(..., description="Company ID"),
    db: AsyncSession = Depends(get_db),
    admin: Admin = Depends(get_current_admin)
):
    """
    Get activity history for a specific lead from ACTIVITIES worksheet
    """
    try:
        # Clean and validate company_id (remove braces, validate UUID)
        company_id = clean_company_id(company_id)
        
        # Validate company_id
        company = await tenant_service.get_company_by_id(db, company_id)
        if not company:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Company not found"
            )
        
        # Verify OAuth connected
        if not company.encrypted_access_token:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Company OAuth not connected"
            )
        
        # Load activities
        activities = await crm_loader_service.get_lead_activities(
            db, company_id, lead_id
        )
        
        logger.info(f"Loaded {len(activities)} activities for lead {lead_id}")
        return activities
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error loading activities for lead {lead_id}: {str(e)}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error loading activities: {str(e)}"
        )


@router.post("/create", response_model=OutboundCreateResponse)
async def create_outbound_email(
    request: OutboundCreateRequest,
    db: AsyncSession = Depends(get_db),
    admin: Admin = Depends(get_current_admin)
):
    """
    Create outbound email draft for a B2B lead
    
    This endpoint:
    1. Validates company_id
    2. Loads lead data from CRM
    3. Loads activity history
    4. Processes through Flow 2 LangGraph workflow
    5. Creates email and draft records
    """
    try:
        # Clean and validate company_id (remove braces, validate UUID)
        request.company_id = clean_company_id(request.company_id)
        
        # Validate company_id
        company = await tenant_service.get_company_by_id(db, request.company_id)
        if not company:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Company not found"
            )
        
        # Verify OAuth connected
        if not company.encrypted_access_token:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Company OAuth not connected. Please connect OAuth first."
            )
        
        # Load lead data from CRM
        lead_data = await crm_loader_service.get_b2b_lead(
            db, request.company_id, request.lead_id
        )
        
        if not lead_data:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Lead {request.lead_id} not found in CRM"
            )
        
        # Load activity history
        activities = await crm_loader_service.get_lead_activities(
            db, request.company_id, request.lead_id
        )
        
        # Initialize Flow 2 Orchestrator
        orchestrator = Flow2Orchestrator()
        
        # Process outbound email
        result = await orchestrator.process_outbound(
            db=db,
            company_id=request.company_id,
            lead_data=lead_data,
            activities=activities,
            intent=request.intent,
            email_type=request.email_type,
            trigger_type=request.trigger_type
        )
        
        if result.get("status") == "error":
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail=result.get("error", "Error processing outbound email")
            )
        
        logger.info(f"Created outbound email {result['email_id']} for lead {request.lead_id}")
        
        return OutboundCreateResponse(
            email_id=result["email_id"],
            draft_id=result["draft_id"],
            status=result["status"],
            subject=result["subject"],
            recipient=result["recipient"],
            lead_stage=lead_data.get("Stage")
        )
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error creating outbound email: {str(e)}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error creating outbound email: {str(e)}"
        )


@router.post("/sent/{draft_id}/update-crm")
async def update_crm_after_send(
    draft_id: str,
    update_data: OutboundUpdateCRMRequest,
    db: AsyncSession = Depends(get_db),
):
    """
    Update CRM sheets after email is sent (LEADS, ACTIVITIES, TASKS — all linked by lead_id).
    No auth required — n8n calls this directly (same as /api/drafts/{id}/sent).
    
    1. Logs email activity to ACTIVITIES (linked to lead_id).
    2. Updates LEADS: Stage, Engagement_Level, Owner, Last_Activity_Date,
       Next_Followup_Date (from PLAYBOOKS.md), Status, Objection_Notes, Notes.
    3. Creates follow-up task in TASKS (linked to lead_id).
    """
    try:
        result = await db.execute(
            select(Draft).where(Draft.id == UUID(draft_id))
        )
        draft = result.scalar_one_or_none()
        if not draft:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Draft not found"
            )
        
        email_result = await db.execute(
            select(Email).where(Email.id == draft.email_id)
        )
        email = email_result.scalar_one_or_none()
        if not email:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Email not found"
            )
        
        # Update CRM for (1) outbound B2B emails and (2) replies in that same thread (inbound with lead_id from thread root).
        is_outbound = (getattr(email, "email_type", None) or "").strip().lower() == "outbound"
        lead_id = (update_data.lead_id or "").strip()
        resolved_lead_from_thread = False
        if not lead_id and not is_outbound and getattr(email, "thread_id", None):
            lead_id = await get_lead_id_from_thread_root(db, str(email.company_id), email.thread_id) or ""
            lead_id = (lead_id or "").strip()
            if lead_id:
                resolved_lead_from_thread = True
                logger.info("CRM update for reply in B2B thread: resolved lead_id=%s from thread", lead_id)
        if not lead_id:
            logger.info(
                "Skipping CRM update: email_type=%s, lead_id empty (CRM only for outbound B2B and their reply thread)",
                getattr(email, "email_type", None),
            )
            return {
                "status": "skipped",
                "message": "CRM update only for outbound B2B emails and their reply thread",
                "lead_id": None,
            }

        company_result = await db.execute(
            select(Company).where(Company.company_id == email.company_id)
        )
        company = company_result.scalar_one_or_none()
        company_name = company.name if company else "System"
        
        company_id = str(email.company_id)
        
        # Next follow-up date: from request, or from company PLAYBOOKS.md (e.g. 3 days after send)
        sent_date = datetime.now()
        today_str = sent_date.strftime('%Y-%m-%d')
        next_followup_date = update_data.next_followup_date
        if not next_followup_date:
            try:
                from services.brand_context_loader import brand_context_loader
                brand_context = await brand_context_loader.load_all(db, company_id)
                playbooks_content = None
                if brand_context and isinstance(brand_context.get("full"), dict):
                    playbooks_content = brand_context["full"].get("playbooks")
                followup_days = parse_followup_days_after_outreach(playbooks_content)
                next_date = sent_date + timedelta(days=followup_days)
                next_followup_date = next_date.strftime('%Y-%m-%d')
            except Exception as e:
                logger.warning(f"Could not load playbook for follow-up days: {e}; using 3 days")
                next_date = sent_date + timedelta(days=3)
                next_followup_date = next_date.strftime('%Y-%m-%d')
        
        if update_data.activity_summary:
            activity_summary = update_data.activity_summary
        elif resolved_lead_from_thread or (not is_outbound and lead_id):
            activity_summary = f"Replied to lead: {email.subject}"
        else:
            activity_summary = f"Sent email: {email.subject}"

        # 1. Log email activity to ACTIVITIES (linked to lead_id)
        await crm_loader_service.log_email_activity(
            db=db,
            company_id=company_id,
            lead_id=lead_id,
            activity_type="email_sent",
            subject_title=email.subject,
            summary=activity_summary,
            performed_by=company_name,
            outcome="Awaiting response",
            next_action=f"Follow up if no response by {next_followup_date}",
            followup_date=next_followup_date
        )
        
        # 2. Update LEADS: Stage, Engagement_Level, Owner, Last_Activity_Date, Next_Followup_Date, Status, Objection_Notes, Notes
        await crm_loader_service.update_lead_after_send(
            db=db,
            company_id=company_id,
            lead_id=lead_id,
            last_activity_date=today_str,
            next_followup_date=next_followup_date,
            stage=update_data.stage or "Email Sent",
            engagement_level=update_data.engagement_level or "Medium",
            owner=update_data.owner or company_name,
            status=update_data.status or "Active",
            objection_notes=update_data.objection_notes,
            notes=update_data.notes,
        )
        
        # 3. Create follow-up task in TASKS (linked to lead_id)
        await crm_loader_service.create_followup_task(
            db=db,
            company_id=company_id,
            lead_id=lead_id,
            task_type="Follow-up Email",
            description=f"Check if lead responded to email: {email.subject}",
            due_date=next_followup_date,
            priority="High",
            assigned_to=company_name
        )
        
        logger.info(f"Updated CRM for lead {lead_id} after sending email (LEADS, ACTIVITIES, TASKS)")
        
        return {
            "status": "success",
            "message": "CRM updated successfully",
            "lead_id": lead_id,
            "activity_logged": True,
            "leads_updated": True,
            "task_created": True,
            "next_followup_date": next_followup_date,
        }
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error updating CRM after send: {str(e)}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error updating CRM: {str(e)}"
        )

