"""
CRM Loader Service
Service to read and write CRM data from Google Sheets in company's Drive folder
"""
from typing import List, Dict, Optional
from sqlalchemy.ext.asyncio import AsyncSession
from services.google_api import google_api_service
from services.token_manager import token_manager_service
from services.tenant import tenant_service
from datetime import datetime, timedelta
import logging
import re

from time_utils import now_ist_str

logger = logging.getLogger(__name__)


class CRMLoaderService:
    """Service for loading and updating CRM data from Google Sheets"""
    
    def __init__(self):
        self.google_api = google_api_service
        self.token_manager = token_manager_service
        self.tenant_service = tenant_service
    
    async def _get_company_drive_folder_id(
        self,
        db: AsyncSession,
        company_id: str
    ) -> Optional[str]:
        """
        Get company's Drive folder ID from database or find it
        
        Args:
            db: Database session
            company_id: Company ID
        
        Returns:
            Drive folder ID or None
        """
        from models.company import Company
        from sqlalchemy import select
        
        # Get company from database
        result = await db.execute(
            select(Company).where(Company.company_id == company_id)
        )
        company = result.scalar_one_or_none()
        
        if not company:
            logger.warning(f"Company {company_id} not found in database")
            return None
        
        # If drive_folder_id is stored, return it
        if company.drive_folder_id:
            logger.info(f"Using stored drive_folder_id for company {company_id}")
            return company.drive_folder_id
        
        # Try to find "CRM" folder directly in My Drive (most common case)
        logger.info(f"Searching for CRM folder for company {company_id}")
        crm_folder_id = await self.google_api.find_folder_by_name(
            db, company_id, "CRM"
        )
        if crm_folder_id:
            logger.info(f"Found CRM folder directly: {crm_folder_id}")
            return crm_folder_id
        
        # If not found, try to find folder by company name, then look for CRM subfolder
        folder_id = await self.google_api.find_folder_by_name(
            db, company_id, company.name
        )
        
        if folder_id:
            logger.info(f"Found company folder {company.name}, looking for CRM subfolder")
            # Look for CRM subfolder inside company folder
            # Note: find_folder_by_name searches globally, so we need to check if it's in the right parent
            crm_folder_id = await self.google_api.find_folder_by_name(
                db, company_id, "CRM"
            )
            if crm_folder_id:
                # Verify it's actually in the company folder
                try:
                    service = await self.google_api.get_drive_service(db, company_id)
                    crm_file = service.files().get(fileId=crm_folder_id, fields="parents").execute()
                    parents = crm_file.get('parents', [])
                    if folder_id in parents:
                        logger.info(f"Found CRM subfolder in company folder: {crm_folder_id}")
                        return crm_folder_id
                except Exception as e:
                    logger.warning(f"Error verifying CRM folder parent: {str(e)}")
        
        logger.warning(f"CRM folder not found for company {company_id}")
        return None
    
    async def _get_crm_workbook(
        self,
        db: AsyncSession,
        company_id: str,
        drive_folder_id: Optional[str] = None
    ) -> Optional[Dict]:
        """
        Find CRM workbook (single file with multiple worksheets)
        
        Looks for "CRM Template.xlsx" or "CRM.xlsx" in CRM folder
        
        Args:
            db: Database session
            company_id: Company ID
            drive_folder_id: Optional Drive folder ID
        
        Returns:
            Dict with 'id' and 'name' if found, None otherwise
        """
        if not drive_folder_id:
            drive_folder_id = await self._get_company_drive_folder_id(db, company_id)
        
        if not drive_folder_id:
            # Try to find CRM folder
            crm_folder_id = await self.google_api.find_folder_by_name(
                db, company_id, "CRM"
            )
            if crm_folder_id:
                drive_folder_id = crm_folder_id
        
        if not drive_folder_id:
            logger.warning(f"CRM folder not found for company {company_id}")
            return None
        
        # Try multiple file name variations
        # Google Sheets files might not have .xlsx extension in the name
        file_name_variations = [
            "CRM Template.xlsx",
            "CRM Template",
            "CRM.xlsx",
            "CRM",
            "CRM Template.XLSX",  # Case variation
        ]
        
        for file_name in file_name_variations:
            logger.info(f"Trying to find spreadsheet: '{file_name}' in folder {drive_folder_id}")
            spreadsheet = await self.google_api.find_spreadsheet_by_name(
                db, company_id, file_name, drive_folder_id
            )
            if spreadsheet:
                logger.info(f"Found CRM workbook: {spreadsheet['name']} (ID: {spreadsheet['id']})")
                return spreadsheet

        # Spreadsheet may be inside a subfolder (e.g. CRM/CRM Template/CRM Template spreadsheet)
        try:
            children = await self.google_api.list_files_in_folder(
                db, company_id, drive_folder_id
            )
            for item in children or []:
                if item.get("mimeType") == "application/vnd.google-apps.folder":
                    subfolder_id = item.get("id")
                    subfolder_name = item.get("name", "")
                    for file_name in file_name_variations:
                        spreadsheet = await self.google_api.find_spreadsheet_by_name(
                            db, company_id, file_name, subfolder_id
                        )
                        if spreadsheet:
                            logger.info(
                                "Found CRM workbook '%s' in subfolder '%s' (ID: %s)",
                                spreadsheet["name"], subfolder_name, spreadsheet["id"]
                            )
                            return spreadsheet
                    # Fallback: any spreadsheet in this subfolder
                    subfolder_sheets = await self.google_api.list_files_in_folder(
                        db, company_id, subfolder_id,
                        mime_type="application/vnd.google-apps.spreadsheet"
                    )
                    if subfolder_sheets:
                        first = subfolder_sheets[0]
                        logger.info(
                            "Using first spreadsheet in subfolder '%s': %s (ID: %s)",
                            subfolder_name, first.get("name"), first.get("id")
                        )
                        return {"id": first["id"], "name": first["name"]}
        except Exception as e:
            logger.warning("Error searching CRM subfolders: %s", e)

        # If still not found, try to use any spreadsheet or Excel file in the CRM folder as fallback
        try:
            service = await self.google_api.get_drive_service(db, company_id)
            
            # First try Google Sheets
            results = service.files().list(
                q=f"'{drive_folder_id}' in parents and mimeType='application/vnd.google-apps.spreadsheet' and trashed=false",
                fields="files(id, name, mimeType)",
                pageSize=10
            ).execute()
            files = results.get('files', [])
            
            # If no Google Sheets, try Excel files
            if not files:
                excel_results = service.files().list(
                    q=f"'{drive_folder_id}' in parents and (mimeType='application/vnd.openxmlformats-officedocument.spreadsheetml.sheet' or mimeType='application/vnd.ms-excel') and trashed=false",
                    fields="files(id, name, mimeType)",
                    pageSize=10
                ).execute()
                excel_files = excel_results.get('files', [])
                
                if excel_files:
                    logger.warning(f"Exact name match failed, but found {len(excel_files)} Excel file(s) in CRM folder. Converting first one to Google Sheets: {excel_files[0]['name']}")
                    # Convert Excel to Google Sheets
                    converted = await self.google_api.convert_excel_to_sheets(
                        db, company_id, excel_files[0]['id'], excel_files[0]['name'], drive_folder_id
                    )
                    return converted
            
            if files:
                # Use the first spreadsheet found as fallback
                logger.info(f"Using first spreadsheet in CRM folder: {files[0]['name']} (ID: {files[0]['id']})")
                return {'id': files[0]['id'], 'name': files[0]['name']}
            else:
                logger.warning(f"No spreadsheets or Excel files found in CRM folder {drive_folder_id}")
        except Exception as e:
            logger.warning(f"Error listing files in CRM folder: {str(e)}")

        # Last resort: search entire Drive for spreadsheet by name (handles wrong folder or nested structure)
        for file_name in ["CRM Template", "CRM Template.xlsx", "CRM"]:
            try:
                spreadsheet = await self.google_api.find_spreadsheet_by_name(
                    db, company_id, file_name, folder_id=None
                )
                if spreadsheet:
                    logger.info(
                        "Found CRM workbook via global search: '%s' (ID: %s). Consider setting company drive_folder_id for faster lookups.",
                        spreadsheet["name"], spreadsheet["id"]
                    )
                    return spreadsheet
            except Exception as e:
                logger.debug("Global search for '%s' failed: %s", file_name, e)
                continue

        logger.warning(f"CRM workbook not found for company {company_id}")
        return None
    
    async def get_b2b_leads(
        self,
        db: AsyncSession,
        company_id: str
    ) -> List[Dict]:
        """
        Get all B2B leads from CRM workbook, LEADS worksheet
        
        Args:
            db: Database session
            company_id: Company ID
        
        Returns:
            List of lead dictionaries with all 18 columns from LEADS worksheet
        """
        try:
            # Find CRM workbook
            spreadsheet = await self._get_crm_workbook(db, company_id)
            
            if not spreadsheet:
                logger.warning(f"CRM workbook not found for company {company_id}")
                return []
            
            # Try to read LEADS worksheet (try different case variations)
            rows = None
            worksheet_names = ["LEADS", "Leads", "leads"]  # Try different cases
            
            for ws_name in worksheet_names:
                try:
                    logger.info(f"Trying to read worksheet: '{ws_name}'")
                    rows = await self.google_api.read_spreadsheet(
                        db, company_id, spreadsheet['id'], ws_name
                    )
                    if rows and len(rows) > 0:
                        logger.info(f"Successfully read {len(rows)} rows from '{ws_name}' worksheet")
                        break
                except Exception as e:
                    logger.warning(f"Error reading worksheet '{ws_name}': {str(e)}")
                    continue
            
            if not rows or len(rows) < 2:
                logger.warning(f"No data found in LEADS worksheet for company {company_id}. Rows: {len(rows) if rows else 0}")
                # Try to list all worksheets for debugging
                try:
                    sheets_service = await self.google_api.get_sheets_service(db, company_id)
                    sheet_metadata = sheets_service.spreadsheets().get(spreadsheetId=spreadsheet['id']).execute()
                    worksheets = sheet_metadata.get('sheets', [])
                    logger.info(f"Available worksheets in workbook: {[ws['properties']['title'] for ws in worksheets]}")
                except Exception as e:
                    logger.warning(f"Error listing worksheets: {str(e)}")
                return []
            
            # Parse header row
            header = rows[0]
            logger.info(f"Header columns: {header}")
            
            # Map column indices
            column_map = {}
            for idx, col_name in enumerate(header):
                column_map[col_name] = idx
            
            # Parse data rows
            leads = []
            total_rows = 0
            active_rows = 0
            for row in rows[1:]:
                if not row or len(row) == 0:
                    continue
                
                total_rows += 1
                
                # Build lead dict
                lead = {}
                for col_name, col_idx in column_map.items():
                    if col_idx < len(row):
                        lead[col_name] = row[col_idx]
                    else:
                        lead[col_name] = None
                
                # Include leads - be very lenient with Status filter
                # Only exclude if Status is explicitly set to something other than Active/active
                status = lead.get('Status', '').strip() if lead.get('Status') else ''
                status_lower = status.lower() if status else ''
                
                # Include lead if:
                # 1. Status is empty/not set
                # 2. Status is 'Active' or 'active'
                # 3. Status column doesn't exist in header
                # Only exclude if Status is explicitly set to something like 'Inactive', 'Closed', etc.
                exclude_statuses = ['inactive', 'closed', 'lost', 'cancelled', 'deleted']
                
                if not status or status_lower == 'active' or status_lower not in exclude_statuses:
                    leads.append(lead)
                    if status_lower == 'active':
                        active_rows += 1
                else:
                    logger.debug(f"Skipping lead {lead.get('Lead_ID', 'unknown')} with Status: '{status}'")
            
            logger.info(f"Loaded {len(leads)} B2B leads for company {company_id} (Total rows: {total_rows}, Active: {active_rows})")
            return leads
            
        except Exception as e:
            logger.error(f"Error loading B2B leads for company {company_id}: {str(e)}")
            raise
    
    async def get_b2b_lead(
        self,
        db: AsyncSession,
        company_id: str,
        lead_id: str
    ) -> Optional[Dict]:
        """
        Get a specific B2B lead by Lead_ID
        
        Args:
            db: Database session
            company_id: Company ID
            lead_id: Lead ID (e.g., "B2B-001")
        
        Returns:
            Lead dictionary or None if not found
        """
        try:
            # Get all leads and find the one with matching Lead_ID
            leads = await self.get_b2b_leads(db, company_id)
            
            for lead in leads:
                if lead.get('Lead_ID') == lead_id:
                    return lead
            
            logger.warning(f"Lead {lead_id} not found for company {company_id}")
            return None
            
        except Exception as e:
            logger.error(f"Error loading lead {lead_id} for company {company_id}: {str(e)}")
            raise
    
    async def get_lead_activities(
        self,
        db: AsyncSession,
        company_id: str,
        lead_id: str
    ) -> List[Dict]:
        """
        Get activity history for a lead from CRM workbook, ACTIVITIES worksheet
        
        Args:
            db: Database session
            company_id: Company ID
            lead_id: Lead ID
        
        Returns:
            List of activity dictionaries, sorted by Activity_Date (most recent first)
        """
        try:
            # Find CRM workbook
            spreadsheet = await self._get_crm_workbook(db, company_id)
            
            if not spreadsheet:
                logger.warning(f"CRM workbook not found for company {company_id}")
                return []
            
            # Read ACTIVITIES worksheet
            rows = await self.google_api.read_spreadsheet(
                db, company_id, spreadsheet['id'], "ACTIVITIES"
            )
            
            if not rows or len(rows) < 2:
                return []
            
            # Parse header row
            header = rows[0]
            column_map = {}
            for idx, col_name in enumerate(header):
                column_map[col_name] = idx
            
            # Filter activities for this lead
            activities = []
            lead_id_idx = self._get_lead_id_column_index(header)
            for row in rows[1:]:
                if not row or len(row) == 0:
                    continue
                if lead_id_idx is None:
                    continue
                # Check if this activity belongs to the lead
                if lead_id_idx < len(row) and str(row[lead_id_idx]).strip() == str(lead_id).strip():
                    activity = {}
                    for col_name, col_idx in column_map.items():
                        if col_idx < len(row):
                            activity[col_name] = row[col_idx]
                        else:
                            activity[col_name] = None
                    activities.append(activity)
            
            # Sort by Activity_Date (most recent first)
            def parse_date(date_str):
                if not date_str:
                    return datetime.min
                try:
                    # Try parsing various date formats
                    for fmt in ['%Y-%m-%d %H:%M:%S', '%Y-%m-%d', '%m/%d/%Y']:
                        try:
                            return datetime.strptime(date_str, fmt)
                        except ValueError:
                            continue
                    return datetime.min
                except:
                    return datetime.min
            
            activities.sort(
                key=lambda x: parse_date(x.get('Activity_Date', '')),
                reverse=True
            )
            
            logger.info(f"Loaded {len(activities)} activities for lead {lead_id}")
            return activities
            
        except Exception as e:
            logger.error(f"Error loading activities for lead {lead_id}: {str(e)}")
            raise
    
    async def _generate_next_activity_id(
        self,
        db: AsyncSession,
        company_id: str
    ) -> str:
        """Generate next Activity_ID in format ACT-XXXX"""
        try:
            spreadsheet = await self._get_crm_workbook(db, company_id)
            
            if not spreadsheet:
                return "ACT-0001"
            
            rows = await self.google_api.read_spreadsheet(
                db, company_id, spreadsheet['id'], "ACTIVITIES"
            )
            
            if not rows or len(rows) < 2:
                return "ACT-0001"
            
            # Find highest Activity_ID
            max_num = 0
            activity_id_idx = None
            if len(rows) > 0:
                header = rows[0]
                for idx, col_name in enumerate(header):
                    if col_name == 'Activity_ID':
                        activity_id_idx = idx
                        break
            
            if activity_id_idx is not None:
                for row in rows[1:]:
                    if activity_id_idx < len(row) and row[activity_id_idx]:
                        activity_id = row[activity_id_idx]
                        match = re.match(r'ACT-(\d+)', activity_id)
                        if match:
                            num = int(match.group(1))
                            max_num = max(max_num, num)
            
            next_num = max_num + 1
            return f"ACT-{next_num:04d}"
            
        except Exception as e:
            logger.warning(f"Error generating Activity_ID: {str(e)}, using default")
            return "ACT-0001"
    
    async def log_email_activity(
        self,
        db: AsyncSession,
        company_id: str,
        lead_id: str,
        activity_type: str,
        subject_title: str,
        summary: str,
        performed_by: str = "System",
        outcome: str = "Awaiting response",
        next_action: Optional[str] = None,
        followup_date: Optional[str] = None
    ) -> Dict:
        """
        Log an email activity to CRM workbook, ACTIVITIES worksheet
        
        Args:
            db: Database session
            company_id: Company ID
            lead_id: Lead ID
            activity_type: Type of activity (e.g., "email_sent")
            subject_title: Email subject
            summary: Activity summary
            performed_by: Who performed the activity
            outcome: Outcome of activity
            next_action: Next action to take
            followup_date: Follow-up date (YYYY-MM-DD format)
        
        Returns:
            Dict with Activity_ID of created activity
        """
        try:
            spreadsheet = await self._get_crm_workbook(db, company_id)
            
            if not spreadsheet:
                raise Exception(f"CRM workbook not found for company {company_id}")
            
            # Read current data to get header
            rows = await self.google_api.read_spreadsheet(
                db, company_id, spreadsheet['id'], "ACTIVITIES"
            )
            
            if not rows or len(rows) == 0:
                raise Exception("ACTIVITIES worksheet is empty or invalid")
            
            header = rows[0]
            column_map = {}
            for idx, col_name in enumerate(header):
                column_map[col_name] = idx
            
            # Generate next Activity_ID
            activity_id = await self._generate_next_activity_id(db, company_id)
            
            # Get current timestamp (app timezone, e.g. IST)
            activity_date = now_ist_str('%Y-%m-%d %H:%M:%S')
            
            # Build row values in correct order
            new_row = []
            for col_name in header:
                if col_name == 'Activity_ID':
                    new_row.append(activity_id)
                elif col_name == 'Lead_ID':
                    new_row.append(lead_id)
                elif col_name == 'Activity_Type':
                    new_row.append(activity_type)
                elif col_name == 'Subject_Title':
                    new_row.append(subject_title)
                elif self._is_summary_column(col_name):
                    new_row.append(summary)
                elif col_name == 'Activity_Date':
                    new_row.append(activity_date)
                elif col_name == 'Performed_By':
                    new_row.append(performed_by)
                elif col_name == 'Outcome':
                    new_row.append(outcome)
                elif col_name == 'Next_Action':
                    new_row.append(next_action or "")
                elif col_name == 'Followup_Date':
                    new_row.append(followup_date or "")
                else:
                    new_row.append("")
            
            # Append row to ACTIVITIES worksheet
            await self.google_api.write_spreadsheet_row(
                db, company_id, spreadsheet['id'], "ACTIVITIES!A:Z", new_row
            )
            
            logger.info(f"Logged activity {activity_id} for lead {lead_id}")
            return {'Activity_ID': activity_id}
            
        except Exception as e:
            logger.error(f"Error logging activity for lead {lead_id}: {str(e)}")
            raise
    
    async def record_lead_replied(
        self,
        db: AsyncSession,
        company_id: str,
        lead_id: str,
        subject: str,
        summary_snippet: str,
        activity_date,
        company_name: str,
        next_action: Optional[str] = None,
    ) -> Optional[Dict]:
        """
        Record a lead-replied activity in CRM workbook, ACTIVITIES worksheet.

        Args:
            db: Database session
            company_id: Company ID
            lead_id: Lead ID
            subject: Email subject
            summary_snippet: Short summary (e.g. "Lead replied to our email. Subject: ...")
            activity_date: When the reply occurred (datetime or str)
            company_name: Company name (for context/logging)
            next_action: Optional next action (e.g. "Review and send reply")

        Returns:
            Dict with Activity_ID or None on failure
        """
        try:
            spreadsheet = await self._get_crm_workbook(db, company_id)
            if not spreadsheet:
                logger.warning(f"CRM workbook not found for company {company_id}")
                return None
            rows = await self.google_api.read_spreadsheet(
                db, company_id, spreadsheet['id'], "ACTIVITIES"
            )
            if not rows or len(rows) == 0:
                logger.warning("ACTIVITIES worksheet is empty or invalid")
                return None
            header = rows[0]
            activity_id = await self._generate_next_activity_id(db, company_id)
            if hasattr(activity_date, 'strftime'):
                activity_date_str = activity_date.strftime('%Y-%m-%d %H:%M:%S')
            else:
                activity_date_str = str(activity_date) if activity_date else now_ist_str('%Y-%m-%d %H:%M:%S')
            column_map = {col_name: idx for idx, col_name in enumerate(header)}
            new_row = []
            for col_name in header:
                if col_name == 'Activity_ID':
                    new_row.append(activity_id)
                elif col_name == 'Lead_ID':
                    new_row.append(lead_id)
                elif col_name == 'Activity_Type':
                    new_row.append('Lead Replied')
                elif col_name == 'Subject_Title':
                    new_row.append(subject or '')
                elif self._is_summary_column(col_name):
                    new_row.append(summary_snippet or '')
                elif col_name == 'Activity_Date':
                    new_row.append(activity_date_str)
                elif col_name == 'Performed_By':
                    new_row.append('System')
                elif col_name == 'Outcome':
                    new_row.append('Reply received')
                elif col_name == 'Next_Action':
                    new_row.append(next_action or 'Review and send reply')
                elif col_name == 'Followup_Date':
                    new_row.append('')
                else:
                    new_row.append('')
            await self.google_api.write_spreadsheet_row(
                db, company_id, spreadsheet['id'], "ACTIVITIES!A:Z", new_row
            )
            logger.info(f"Recorded lead replied activity {activity_id} for lead {lead_id} ({company_name})")
            return {'Activity_ID': activity_id}
        except Exception as e:
            logger.error(f"Error recording lead replied for lead {lead_id}: {str(e)}")
            return None
    
    async def update_lead_activity_dates(
        self,
        db: AsyncSession,
        company_id: str,
        lead_id: str,
        last_activity_date: str,
        next_followup_date: str
    ) -> bool:
        """
        Update Last_Activity_Date and Next_Followup_Date in CRM workbook, LEADS worksheet
        
        Args:
            db: Database session
            company_id: Company ID
            lead_id: Lead ID
            last_activity_date: Date in YYYY-MM-DD format
            next_followup_date: Date in YYYY-MM-DD format
        
        Returns:
            True if successful
        """
        try:
            spreadsheet = await self._get_crm_workbook(db, company_id)
            
            if not spreadsheet:
                raise Exception(f"CRM workbook not found for company {company_id}")
            
            # Read current data from LEADS worksheet
            rows = await self.google_api.read_spreadsheet(
                db, company_id, spreadsheet['id'], "LEADS"
            )
            
            if not rows or len(rows) < 2:
                raise Exception("LEADS worksheet is empty or invalid")
            
            header = rows[0]
            column_map = {str(col).strip(): i for i, col in enumerate(header)}
            lead_id_idx = self._get_lead_id_column_index(header)
            last_activity_idx = column_map.get('Last_Activity_Date')
            next_followup_idx = column_map.get('Next_Followup_Date')
            
            if lead_id_idx is None:
                raise Exception(f"Lead_ID or ID column not found in LEADS worksheet. Columns found: {list(column_map.keys())}")
            
            # Find row with matching Lead_ID or ID
            row_num = self._find_leads_row_by_lead_id(rows, header, lead_id, lead_id_idx)
            if row_num is None:
                raise Exception(f"Lead {lead_id} not found in LEADS worksheet")
            
            # Update cells in LEADS worksheet
            if last_activity_idx is not None:
                col_letter = self._col_letter(last_activity_idx)
                range_name = f"LEADS!{col_letter}{row_num}"
                await self.google_api.update_spreadsheet_cell(
                    db, company_id, spreadsheet['id'], range_name, last_activity_date
                )
            if next_followup_idx is not None:
                col_letter = self._col_letter(next_followup_idx)
                range_name = f"LEADS!{col_letter}{row_num}"
                await self.google_api.update_spreadsheet_cell(
                    db, company_id, spreadsheet['id'], range_name, next_followup_date
                )
            
            logger.info(f"Updated activity dates for lead {lead_id}")
            return True
            
        except Exception as e:
            logger.error(f"Error updating activity dates for lead {lead_id}: {str(e)}")
            raise
    
    async def update_lead_stage(
        self,
        db: AsyncSession,
        company_id: str,
        lead_id: str,
        new_stage: str
    ) -> bool:
        """
        Update Stage column in CRM workbook, LEADS worksheet
        
        Args:
            db: Database session
            company_id: Company ID
            lead_id: Lead ID
            new_stage: New stage value
        
        Returns:
            True if successful
        """
        try:
            spreadsheet = await self._get_crm_workbook(db, company_id)
            
            if not spreadsheet:
                raise Exception(f"CRM workbook not found for company {company_id}")
            
            # Read current data from LEADS worksheet
            rows = await self.google_api.read_spreadsheet(
                db, company_id, spreadsheet['id'], "LEADS"
            )
            
            if not rows or len(rows) < 2:
                raise Exception("LEADS worksheet is empty or invalid")
            
            header = rows[0]
            lead_id_idx = self._get_lead_id_column_index(header)
            stage_idx = next((i for i, c in enumerate(header) if str(c).strip() == 'Stage'), None)
            
            if lead_id_idx is None:
                raise Exception("Lead_ID or ID column not found in LEADS worksheet")
            
            if stage_idx is None:
                raise Exception("Stage column not found in LEADS worksheet")
            
            row_num = self._find_leads_row_by_lead_id(rows, header, lead_id, lead_id_idx)
            if row_num is None:
                raise Exception(f"Lead {lead_id} not found in LEADS worksheet")
            
            col_letter = self._col_letter(stage_idx)
            range_name = f"LEADS!{col_letter}{row_num}"
            await self.google_api.update_spreadsheet_cell(
                db, company_id, spreadsheet['id'], range_name, new_stage
            )
            
            logger.info(f"Updated stage for lead {lead_id} to {new_stage}")
            return True
            
        except Exception as e:
            logger.error(f"Error updating stage for lead {lead_id}: {str(e)}")
            raise
    
    def _col_letter(self, idx: int) -> str:
        """Convert 0-based column index to A1 notation (A, B, ..., Z, AA, AB, ...)."""
        if idx < 26:
            return chr(ord('A') + idx)
        return self._col_letter((idx // 26) - 1) + chr(ord('A') + (idx % 26))

    def _get_lead_id_column_index(self, header: List) -> Optional[int]:
        """
        Return 0-based index of Lead_ID / ID column in LEADS header.
        Case-insensitive; accepts 'Lead_ID', 'Lead ID', 'lead_id', 'ID', 'Id'.
        """
        for idx, col in enumerate(header):
            c = str(col).strip() if col is not None else ""
            n = c.replace(" ", "_").lower()
            if n == "lead_id":
                return idx
        for idx, col in enumerate(header):
            c = str(col).strip() if col is not None else ""
            if c.lower() == "id":
                return idx
        return None

    @staticmethod
    def _is_summary_column(col_name: str) -> bool:
        """True if column is Summary (case-insensitive). Used for ACTIVITIES Summary column."""
        return col_name is not None and str(col_name).strip().lower() == "summary"

    def _find_leads_row_by_lead_id(
        self, rows: List[List], header: List, lead_id: str, lead_id_idx: Optional[int] = None
    ) -> Optional[int]:
        """Find LEADS data row number (1-based, header=1) for the given lead_id. Supports Lead_ID or ID column."""
        if lead_id_idx is None:
            lead_id_idx = self._get_lead_id_column_index(header)
        if lead_id_idx is None:
            return None
        for idx, row in enumerate(rows[1:], start=2):
            if lead_id_idx < len(row) and str(row[lead_id_idx]).strip() == str(lead_id).strip():
                return idx
        return None

    async def get_lead_follow_up_count(
        self,
        db: AsyncSession,
        company_id: str,
        lead_id: str,
    ) -> int:
        """
        Read current Follow_Up_Count for a lead from LEADS worksheet.
        Returns 0 if column missing or value missing/non-numeric.
        """
        try:
            spreadsheet = await self._get_crm_workbook(db, company_id)
            if not spreadsheet:
                return 0
            rows = await self.google_api.read_spreadsheet(
                db, company_id, spreadsheet['id'], "LEADS"
            )
            if not rows or len(rows) < 2:
                return 0
            header = [str(h).strip() for h in rows[0]]
            column_map = {col: idx for idx, col in enumerate(header)}
            lead_id_idx = self._get_lead_id_column_index(header)
            follow_up_idx = column_map.get('Follow_Up_Count')
            if lead_id_idx is None or follow_up_idx is None:
                return 0
            for row in rows[1:]:
                if lead_id_idx < len(row) and str(row[lead_id_idx]).strip() == str(lead_id).strip():
                    val = row[follow_up_idx] if follow_up_idx < len(row) else None
                    if val is None or val == "":
                        return 0
                    try:
                        return int(float(str(val).strip()))
                    except (ValueError, TypeError):
                        return 0
            return 0
        except Exception as e:
            logger.warning("Could not read Follow_Up_Count for lead %s: %s", lead_id, e)
            return 0

    async def update_lead_after_send(
        self,
        db: AsyncSession,
        company_id: str,
        lead_id: str,
        last_activity_date: str,
        next_followup_date: str,
        stage: str = "Email Sent",
        engagement_level: str = "Medium",
        owner: Optional[str] = None,
        status: str = "Active",
        objection_notes: Optional[str] = None,
        notes: Optional[str] = None,
        follow_up_count: Optional[int] = None,
    ) -> bool:
        """
        Update LEADS row after outbound email is sent: Stage, Engagement_Level, Owner,
        Last_Activity_Date, Next_Followup_Date, Status, Follow_Up_Count, Objection_Notes, Notes.
        Row is found by Lead_ID or ID. Only columns present in the sheet are updated.
        """
        try:
            spreadsheet = await self._get_crm_workbook(db, company_id)
            if not spreadsheet:
                raise Exception(f"CRM workbook not found for company {company_id}")
            
            rows = await self.google_api.read_spreadsheet(
                db, company_id, spreadsheet['id'], "LEADS"
            )
            if not rows or len(rows) < 2:
                raise Exception("LEADS worksheet is empty or invalid")
            
            header = rows[0]
            column_map = {str(col).strip(): idx for idx, col in enumerate(header)}
            lead_id_idx = self._get_lead_id_column_index(header)
            if lead_id_idx is None:
                raise Exception(f"Lead_ID or ID column not found in LEADS worksheet. Columns found: {list(column_map.keys())}")
            
            row_num = self._find_leads_row_by_lead_id(rows, header, lead_id, lead_id_idx)
            if row_num is None:
                raise Exception(f"Lead {lead_id} not found in LEADS worksheet")
            
            # Map field -> (column_name, value); only update if column exists
            updates = []
            if 'Stage' in column_map:
                updates.append(('Stage', stage))
            if 'Engagement_Level' in column_map:
                updates.append(('Engagement_Level', engagement_level))
            if owner is not None and 'Owner' in column_map:
                updates.append(('Owner', owner))
            if 'Last_Activity_Date' in column_map:
                updates.append(('Last_Activity_Date', last_activity_date))
            if 'Next_Followup_Date' in column_map:
                updates.append(('Next_Followup_Date', next_followup_date))
            if 'Status' in column_map:
                updates.append(('Status', status))
            if follow_up_count is not None and 'Follow_Up_Count' in column_map:
                updates.append(('Follow_Up_Count', str(follow_up_count)))
            if objection_notes is not None and 'Objection_Notes' in column_map:
                updates.append(('Objection_Notes', objection_notes))
            if notes is not None and 'Notes' in column_map:
                updates.append(('Notes', notes))
            
            for col_name, value in updates:
                idx = column_map[col_name]
                col_letter = self._col_letter(idx)
                range_name = f"LEADS!{col_letter}{row_num}"
                await self.google_api.update_spreadsheet_cell(
                    db, company_id, spreadsheet['id'], range_name, value or ""
                )
            
            logger.info(
                "Updated LEADS for lead %s: Stage=%s, Last_Activity_Date=%s, Next_Followup_Date=%s",
                lead_id, stage, last_activity_date, next_followup_date
            )
            return True
        except Exception as e:
            logger.error(f"Error updating lead after send for lead {lead_id}: {str(e)}")
            raise

    async def update_lead_outreach_stopped(
        self,
        db: AsyncSession,
        company_id: str,
        lead_id: str,
    ) -> bool:
        """
        Set lead Status (or Stage) to "No Response – Outreach Stopped".
        Used when Follow_Up_Count is 2 and still no reply by next follow-up date.
        """
        try:
            spreadsheet = await self._get_crm_workbook(db, company_id)
            if not spreadsheet:
                raise Exception(f"CRM workbook not found for company {company_id}")
            rows = await self.google_api.read_spreadsheet(
                db, company_id, spreadsheet['id'], "LEADS"
            )
            if not rows or len(rows) < 2:
                raise Exception("LEADS worksheet is empty or invalid")
            header = rows[0]
            column_map = {str(col).strip(): idx for idx, col in enumerate(header)}
            lead_id_idx = self._get_lead_id_column_index(header)
            if lead_id_idx is None:
                raise Exception(f"Lead_ID or ID column not found in LEADS worksheet. Columns found: {list(column_map.keys())}")
            row_num = self._find_leads_row_by_lead_id(rows, header, lead_id, lead_id_idx)
            if row_num is None:
                raise Exception(f"Lead {lead_id} not found in LEADS worksheet")
            stopped_value = "No Response – Outreach Stopped"
            updates = []
            if 'Status' in column_map:
                updates.append(('Status', stopped_value))
            if 'Stage' in column_map:
                updates.append(('Stage', stopped_value))
            for col_name, value in updates:
                idx = column_map[col_name]
                col_letter = self._col_letter(idx)
                range_name = f"LEADS!{col_letter}{row_num}"
                await self.google_api.update_spreadsheet_cell(
                    db, company_id, spreadsheet['id'], range_name, value
                )
            logger.info("Marked lead %s as No Response – Outreach Stopped", lead_id)
            return True
        except Exception as e:
            logger.error(f"Error marking lead outreach stopped for lead {lead_id}: {str(e)}")
            raise

    async def _generate_next_task_id(
        self,
        db: AsyncSession,
        company_id: str
    ) -> str:
        """Generate next Task_ID in format TASK-XXXX"""
        try:
            spreadsheet = await self._get_crm_workbook(db, company_id)
            
            if not spreadsheet:
                return "TASK-0001"
            
            rows = await self.google_api.read_spreadsheet(
                db, company_id, spreadsheet['id'], "TASKS"
            )
            
            if not rows or len(rows) < 2:
                return "TASK-0001"
            
            # Find highest Task_ID
            max_num = 0
            task_id_idx = None
            if len(rows) > 0:
                header = rows[0]
                for idx, col_name in enumerate(header):
                    if col_name == 'Task_ID':
                        task_id_idx = idx
                        break
            
            if task_id_idx is not None:
                for row in rows[1:]:
                    if task_id_idx < len(row) and row[task_id_idx]:
                        task_id = row[task_id_idx]
                        match = re.match(r'TASK-(\d+)', task_id)
                        if match:
                            num = int(match.group(1))
                            max_num = max(max_num, num)
            
            next_num = max_num + 1
            return f"TASK-{next_num:04d}"
            
        except Exception as e:
            logger.warning(f"Error generating Task_ID: {str(e)}, using default")
            return "TASK-0001"
    
    async def create_followup_task(
        self,
        db: AsyncSession,
        company_id: str,
        lead_id: str,
        task_type: str,
        description: str,
        due_date: str,
        priority: str = "High",
        assigned_to: str = "System"
    ) -> Dict:
        """
        Create a follow-up task in CRM workbook, TASKS worksheet
        
        Args:
            db: Database session
            company_id: Company ID
            lead_id: Lead ID
            task_type: Type of task (e.g., "Follow-up Email")
            description: Task description
            due_date: Due date in YYYY-MM-DD format
            priority: Priority level (High, Medium, Low)
            assigned_to: Who the task is assigned to
        
        Returns:
            Dict with Task_ID of created task
        """
        try:
            spreadsheet = await self._get_crm_workbook(db, company_id)
            
            if not spreadsheet:
                raise Exception(f"CRM workbook not found for company {company_id}")
            
            # Read current data to get header from TASKS worksheet
            rows = await self.google_api.read_spreadsheet(
                db, company_id, spreadsheet['id'], "TASKS"
            )
            
            if not rows or len(rows) == 0:
                raise Exception("TASKS worksheet is empty or invalid")
            
            header = rows[0]
            
            # Generate next Task_ID
            task_id = await self._generate_next_task_id(db, company_id)
            
            # Build row values in correct order
            new_row = []
            for col_name in header:
                if col_name == 'Task_ID':
                    new_row.append(task_id)
                elif col_name == 'Lead_ID':
                    new_row.append(lead_id)
                elif col_name == 'Task_Type':
                    new_row.append(task_type)
                elif col_name == 'Description':
                    new_row.append(description)
                elif col_name == 'Due_Date':
                    new_row.append(due_date)
                elif col_name == 'Priority':
                    new_row.append(priority)
                elif col_name == 'Status':
                    new_row.append("Pending")
                elif col_name == 'Assigned_To':
                    new_row.append(assigned_to)
                else:
                    new_row.append("")
            
            # Append row to TASKS worksheet
            await self.google_api.write_spreadsheet_row(
                db, company_id, spreadsheet['id'], "TASKS!A:Z", new_row
            )
            
            logger.info(f"Created task {task_id} for lead {lead_id}")
            return {'Task_ID': task_id}
            
        except Exception as e:
            logger.error(f"Error creating task for lead {lead_id}: {str(e)}")
            raise

    async def mark_tasks_completed_for_lead_reply(
        self,
        db: AsyncSession,
        company_id: str,
        lead_id: str,
    ) -> int:
        """
        Mark pending follow-up tasks for this lead as Completed when lead has replied.
        Matches tasks where Lead_ID = lead_id, Status = Pending, and Description
        contains "Check if lead respond" or "Follow-up Email" / "Follow-up".
        Returns number of tasks updated.
        """
        try:
            spreadsheet = await self._get_crm_workbook(db, company_id)
            if not spreadsheet:
                return 0
            rows = await self.google_api.read_spreadsheet(
                db, company_id, spreadsheet['id'], "TASKS"
            )
            if not rows or len(rows) < 2:
                return 0
            header = [str(h).strip() for h in rows[0]]
            lead_id_idx = self._get_lead_id_column_index(header)
            desc_idx = next((i for i, c in enumerate(header) if c == 'Description'), None)
            status_idx = next((i for i, c in enumerate(header) if c == 'Status'), None)
            if lead_id_idx is None or desc_idx is None or status_idx is None:
                return 0
            keywords = ("check if lead respond", "follow-up email", "follow-up", "follow up")
            updated = 0
            for row_num, row in enumerate(rows[1:], start=2):
                if lead_id_idx >= len(row) or str(row[lead_id_idx]).strip() != str(lead_id).strip():
                    continue
                status = str(row[status_idx]).strip() if status_idx < len(row) else ""
                if status.lower() != "pending":
                    continue
                desc = (row[desc_idx] or "").strip().lower() if desc_idx < len(row) else ""
                if not any(k in desc for k in keywords):
                    continue
                col_letter = self._col_letter(status_idx)
                range_name = f"TASKS!{col_letter}{row_num}"
                await self.google_api.update_spreadsheet_cell(
                    db, company_id, spreadsheet['id'], range_name, "Completed"
                )
                updated += 1
            if updated:
                logger.info("Marked %s task(s) Completed for lead %s (lead replied)", updated, lead_id)
            return updated
        except Exception as e:
            logger.warning("Could not mark tasks completed for lead reply (lead_id=%s): %s", lead_id, e)
            return 0

    async def mark_review_reply_tasks_completed_after_send(
        self,
        db: AsyncSession,
        company_id: str,
        lead_id: str,
        send_date_str: str,
    ) -> int:
        """
        When we send a reply to a lead, mark "Review Reply" / "Review lead reply" tasks
        for this lead as Completed and set Due_Date to send_date_str.
        Matches tasks where Lead_ID = lead_id, Status = Pending, and (Task_Type or Description)
        contains "Review Reply" or "Review lead reply".
        Returns number of tasks updated.
        """
        try:
            spreadsheet = await self._get_crm_workbook(db, company_id)
            if not spreadsheet:
                return 0
            rows = await self.google_api.read_spreadsheet(
                db, company_id, spreadsheet['id'], "TASKS"
            )
            if not rows or len(rows) < 2:
                return 0
            header = [str(h).strip() for h in rows[0]]
            lead_id_idx = self._get_lead_id_column_index(header)
            task_type_idx = next((i for i, c in enumerate(header) if str(c).strip().lower() == 'task_type'), None)
            desc_idx = next((i for i, c in enumerate(header) if str(c).strip() == 'Description'), None)
            status_idx = next((i for i, c in enumerate(header) if str(c).strip() == 'Status'), None)
            due_date_idx = next((i for i, c in enumerate(header) if str(c).strip() == 'Due_Date'), None)
            if lead_id_idx is None or status_idx is None:
                return 0
            review_keywords = ("review reply", "review lead reply")
            updated = 0
            for row_num, row in enumerate(rows[1:], start=2):
                if lead_id_idx >= len(row) or str(row[lead_id_idx]).strip() != str(lead_id).strip():
                    continue
                status = str(row[status_idx]).strip() if status_idx < len(row) else ""
                if status.lower() != "pending":
                    continue
                desc = (row[desc_idx] or "").strip().lower() if desc_idx is not None and desc_idx < len(row) else ""
                task_type = (row[task_type_idx] or "").strip().lower() if task_type_idx is not None and task_type_idx < len(row) else ""
                combined = f"{task_type} {desc}"
                if not any(k in combined for k in review_keywords):
                    continue
                # Update Status to Completed
                col_letter = self._col_letter(status_idx)
                range_name = f"TASKS!{col_letter}{row_num}"
                await self.google_api.update_spreadsheet_cell(
                    db, company_id, spreadsheet['id'], range_name, "Completed"
                )
                # Update Due_Date to send date
                if due_date_idx is not None:
                    due_col_letter = self._col_letter(due_date_idx)
                    due_range = f"TASKS!{due_col_letter}{row_num}"
                    await self.google_api.update_spreadsheet_cell(
                        db, company_id, spreadsheet['id'], due_range, send_date_str
                    )
                updated += 1
            if updated:
                logger.info("Marked %s Review Reply task(s) Completed for lead %s (reply sent)", updated, lead_id)
            return updated
        except Exception as e:
            logger.warning("Could not mark Review Reply tasks completed (lead_id=%s): %s", lead_id, e)
            return 0


# Singleton instance
crm_loader_service = CRMLoaderService()

