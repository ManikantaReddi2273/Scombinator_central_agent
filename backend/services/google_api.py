"""
Google API service for Drive and Gmail access
"""
from typing import List, Dict, Optional
from sqlalchemy.ext.asyncio import AsyncSession
from services.token_manager import token_manager_service
from googleapiclient.discovery import build
from googleapiclient.errors import HttpError
import io
from googleapiclient.http import MediaIoBaseDownload
import logging

logger = logging.getLogger(__name__)


class GoogleAPIService:
    """Service for interacting with Google APIs"""
    
    def __init__(self):
        self.token_manager = token_manager_service
    
    async def get_drive_service(self, db: AsyncSession, company_id: str):
        """Get Google Drive service instance"""
        credentials = await self.token_manager.get_credentials(db, company_id)
        return build('drive', 'v3', credentials=credentials)
    
    async def get_gmail_service(self, db: AsyncSession, company_id: str):
        """Get Gmail service instance"""
        credentials = await self.token_manager.get_credentials(db, company_id)
        return build('gmail', 'v1', credentials=credentials)
    
    async def get_sheets_service(self, db: AsyncSession, company_id: str):
        """Get Google Sheets service instance"""
        credentials = await self.token_manager.get_credentials(db, company_id)
        return build('sheets', 'v4', credentials=credentials)
    
    async def list_drive_files(
        self,
        db: AsyncSession,
        company_id: str,
        folder_path: str,
        mime_type: Optional[str] = None
    ) -> List[Dict]:
        """List files in a Drive folder"""
        try:
            service = await self.get_drive_service(db, company_id)
            
            # Search for files in folder (simplified - in production, use proper folder ID)
            query = f"name contains '{folder_path.split('/')[-1]}'"
            if mime_type:
                query += f" and mimeType = '{mime_type}'"
            
            results = service.files().list(
                q=query,
                fields="files(id, name, mimeType, modifiedTime)"
            ).execute()
            
            return results.get('files', [])
        except HttpError as error:
            raise Exception(f"Error listing Drive files: {error}")
    
    async def read_drive_file(
        self,
        db: AsyncSession,
        company_id: str,
        file_id: str
    ) -> str:
        """Read content of a Drive file"""
        try:
            service = await self.get_drive_service(db, company_id)
            
            # Get file metadata
            file_metadata = service.files().get(fileId=file_id).execute()
            
            # Download file content
            request = service.files().get_media(fileId=file_id)
            file_content = io.BytesIO()
            downloader = MediaIoBaseDownload(file_content, request)
            
            done = False
            while not done:
                status, done = downloader.next_chunk()
            
            return file_content.getvalue().decode('utf-8')
        except HttpError as error:
            raise Exception(f"Error reading Drive file: {error}")
    
    async def read_drive_file_by_name(
        self,
        db: AsyncSession,
        company_id: str,
        file_name: str,
        folder_path: Optional[str] = None
    ) -> Optional[str]:
        """Read Drive file by name (searches in folder if provided)"""
        try:
            service = await self.get_drive_service(db, company_id)
            
            # Build query
            query = f"name = '{file_name}'"
            if folder_path:
                # In production, resolve folder ID properly
                folder_name = folder_path.split('/')[-1]
                query += f" and '{folder_name}' in parents"
            
            results = service.files().list(
                q=query,
                fields="files(id, name)"
            ).execute()
            
            files = results.get('files', [])
            if not files:
                return None
            
            # Read first matching file
            return await self.read_drive_file(db, company_id, files[0]['id'])
        except HttpError as error:
            raise Exception(f"Error reading Drive file by name: {error}")
    
    async def get_policy_files(
        self,
        db: AsyncSession,
        company_id: str,
        company_name: str
    ) -> Dict[str, Optional[str]]:
        """Get all policy files for a company from Drive"""
        policies = {}
        
        # List of policy files to fetch
        policy_files = [
            f"{company_name}/policies/brand_tone.txt",
            f"{company_name}/policies/pricing_rules.pdf",
            f"{company_name}/templates/email_template_1.txt",
            f"{company_name}/templates/faq.json",
        ]
        
        for file_path in policy_files:
            file_name = file_path.split('/')[-1]
            folder_path = '/'.join(file_path.split('/')[:-1])
            
            try:
                content = await self.read_drive_file_by_name(
                    db, company_id, file_name, folder_path
                )
                policies[file_name] = content
            except Exception as e:
                # Log error but continue
                policies[file_name] = None
        
        return policies

    async def get_template_files(
        self,
        db: AsyncSession,
        company_id: str,
        company_name: str
    ) -> Dict[str, Optional[str]]:
        """Get email template files for a company from Drive"""
        templates = {}
        
        # List of template files to fetch
        template_files = [
            f"{company_name}/templates/pricing_inquiry_template.txt",
            f"{company_name}/templates/support_response_template.txt",
            f"{company_name}/templates/general_response_template.txt",
            f"{company_name}/templates/application_acknowledgment_template.txt",
            f"{company_name}/templates/email_template_1.txt",
            f"{company_name}/templates/email_template_2.txt",
        ]
        
        for file_path in template_files:
            file_name = file_path.split('/')[-1]
            folder_path = '/'.join(file_path.split('/')[:-1])
            
            try:
                content = await self.read_drive_file_by_name(
                    db, company_id, file_name, folder_path
                )
                if content:
                    templates[file_name] = content
            except Exception as e:
                # Log error but continue
                import logging
                logger = logging.getLogger(__name__)
                logger.debug(f"Template {file_name} not found in Drive: {str(e)}")
                continue
        
        return templates
    
    async def find_folder_by_name(
        self,
        db: AsyncSession,
        company_id: str,
        folder_name: str
    ) -> Optional[str]:
        """
        Find folder by name in Google Drive
        
        Args:
            db: Database session
            company_id: Company ID
            folder_name: Name of folder to find
            
        Returns:
            Folder ID if found, None otherwise
        """
        try:
            service = await self.get_drive_service(db, company_id)
            
            # Search for folder by exact name
            query = f"name='{folder_name}' and mimeType='application/vnd.google-apps.folder' and trashed=false"
            
            results = service.files().list(
                q=query,
                fields="files(id, name)",
                pageSize=10
            ).execute()
            
            folders = results.get('files', [])
            if folders:
                logger.info(f"Found folder '{folder_name}' with ID: {folders[0]['id']}")
                return folders[0]['id']
            
            logger.debug(f"Folder '{folder_name}' not found")
            return None
        except HttpError as error:
            logger.error(f"Error finding folder '{folder_name}': {error}")
            raise Exception(f"Error finding folder: {error}")
    
    async def list_files_in_folder(
        self,
        db: AsyncSession,
        company_id: str,
        folder_id: str,
        mime_type: Optional[str] = None
    ) -> List[Dict]:
        """
        List all files in a folder
        
        Args:
            db: Database session
            company_id: Company ID
            folder_id: ID of the folder
            mime_type: Optional MIME type filter
            
        Returns:
            List of file metadata dicts (id, name, mimeType)
        """
        try:
            service = await self.get_drive_service(db, company_id)
            
            # Build query
            query = f"'{folder_id}' in parents and trashed=false"
            if mime_type:
                query += f" and mimeType='{mime_type}'"
            
            all_files = []
            page_token = None
            
            # Handle pagination
            while True:
                results = service.files().list(
                    q=query,
                    fields="nextPageToken, files(id, name, mimeType)",
                    pageSize=100,
                    pageToken=page_token
                ).execute()
                
                files = results.get('files', [])
                all_files.extend(files)
                
                page_token = results.get('nextPageToken')
                if not page_token:
                    break
            
            logger.debug(f"Found {len(all_files)} files in folder {folder_id}")
            return all_files
        except HttpError as error:
            logger.error(f"Error listing files in folder {folder_id}: {error}")
            raise Exception(f"Error listing files in folder: {error}")
    
    async def load_brand_context_folder(
        self,
        db: AsyncSession,
        company_id: str,
        company_name: str
    ) -> Dict[str, Optional[str]]:
        """
        Load all brand context files from Google Drive
        
        Looks for "Brand Context Documents" folder, or falls back to company name folder.
        Loads: COMPANY.md, VOICE.md, PLAYBOOKS.md, POLICIES.md, KNOWLEDGE.md, and TEMPLATES/
        
        Args:
            db: Database session
            company_id: Company ID
            company_name: Company name (for fallback folder search)
            
        Returns:
            Dict with keys: company, voice, playbooks, policies, knowledge, templates
            Missing files will have None values
        """
        brand_context = {
            "company": None,
            "voice": None,
            "playbooks": None,
            "policies": None,
            "knowledge": None,
            "templates": {}
        }
        
        try:
            # Try to find "Brand Context Documents" folder first
            folder_id = await self.find_folder_by_name(db, company_id, "Brand Context Documents")
            
            # If not found, try company name folder
            if not folder_id:
                folder_id = await self.find_folder_by_name(db, company_id, company_name)
            
            if not folder_id:
                logger.warning(f"Brand context folder not found for {company_name}")
                return brand_context
            
            # List all files in the folder
            files = await self.list_files_in_folder(db, company_id, folder_id)
            
            # Load main documents (COMPANY.md, VOICE.md, etc.)
            doc_names = ["COMPANY.md", "VOICE.md", "PLAYBOOKS.md", "POLICIES.md", "KNOWLEDGE.md"]
            for file_info in files:
                file_name = file_info['name']
                if file_name in doc_names:
                    try:
                        content = await self.read_drive_file(db, company_id, file_info['id'])
                        # Store without .md extension as key (lowercase)
                        key = file_name.replace('.md', '').lower()
                        brand_context[key] = content
                        logger.info(f"Loaded {file_name} for company {company_name}")
                    except Exception as e:
                        logger.warning(f"Error loading {file_name}: {str(e)}")
                        key = file_name.replace('.md', '').lower()
                        brand_context[key] = None
            
            # Find and load TEMPLATES folder
            templates_folder_id = None
            for file_info in files:
                if file_info['name'] == "TEMPLATES" and file_info['mimeType'] == 'application/vnd.google-apps.folder':
                    templates_folder_id = file_info['id']
                    break
            
            if templates_folder_id:
                templates = {}
                # List all files in TEMPLATES folder (including subfolders)
                template_files = await self.list_files_in_folder(db, company_id, templates_folder_id)
                
                # Also check subfolders (outreach/, hiring/, responses/)
                for file_info in template_files:
                    # If it's a subfolder, list files inside it
                    if file_info['mimeType'] == 'application/vnd.google-apps.folder':
                        subfolder_name = file_info['name']
                        subfolder_files = await self.list_files_in_folder(db, company_id, file_info['id'])
                        for sub_file in subfolder_files:
                            # Store with subfolder prefix: "outreach/template_name.md"
                            template_key = f"{subfolder_name}/{sub_file['name']}"
                            try:
                                content = await self.read_drive_file(db, company_id, sub_file['id'])
                                templates[template_key] = content
                                logger.debug(f"Loaded template: {template_key}")
                            except Exception as e:
                                logger.warning(f"Error loading template {template_key}: {str(e)}")
                    else:
                        # Direct template file in TEMPLATES folder
                        template_name = file_info['name']
                        # Only load text/markdown files
                        if file_info['mimeType'] in ['text/plain', 'text/markdown'] or template_name.endswith('.md'):
                            try:
                                content = await self.read_drive_file(db, company_id, file_info['id'])
                                templates[template_name] = content
                                logger.debug(f"Loaded template: {template_name}")
                            except Exception as e:
                                logger.warning(f"Error loading template {template_name}: {str(e)}")
                
                brand_context['templates'] = templates
                logger.info(f"Loaded {len(templates)} templates for company {company_name}")
            
            return brand_context
            
        except Exception as e:
            logger.error(f"Error loading brand context folder for {company_name}: {str(e)}")
            return brand_context
    
    async def read_spreadsheet(
        self,
        db: AsyncSession,
        company_id: str,
        spreadsheet_id: str,
        range_name: Optional[str] = None
    ) -> List[List[str]]:
        """
        Read data from a Google Sheets spreadsheet
        
        Args:
            db: Database session
            company_id: Company ID
            spreadsheet_id: Google Sheets spreadsheet ID (from file ID)
            range_name: Optional A1 notation range (e.g., "Sheet1!A1:Z100" or just "Sheet1"). 
                       If None, reads entire first sheet.
                       Can be just worksheet name (e.g., "LEADS") or full range (e.g., "LEADS!A:Z")
        
        Returns:
            List of rows, where each row is a list of cell values
        """
        try:
            service = await self.get_sheets_service(db, company_id)
            
            # If no range specified, read entire first sheet
            if not range_name:
                range_name = "Sheet1"
            # If range_name is just a worksheet name (no !), add !A:Z to read entire sheet
            elif '!' not in range_name:
                range_name = f"{range_name}!A:Z"
            
            logger.debug(f"Reading spreadsheet {spreadsheet_id} with range: {range_name}")
            
            result = service.spreadsheets().values().get(
                spreadsheetId=spreadsheet_id,
                range=range_name
            ).execute()
            
            values = result.get('values', [])
            logger.debug(f"Read {len(values)} rows from spreadsheet {spreadsheet_id}, range {range_name}")
            return values
        except HttpError as error:
            error_details = str(error)
            logger.error(f"Error reading spreadsheet {spreadsheet_id}, range {range_name}: {error_details}")
            # Provide more helpful error message
            if "Unable to parse range" in error_details or "Unable to parse" in error_details:
                raise Exception(f"Worksheet '{range_name}' not found. Please check the worksheet name matches exactly (case-sensitive).")
            raise Exception(f"Error reading spreadsheet: {error_details}")
    
    async def write_spreadsheet_row(
        self,
        db: AsyncSession,
        company_id: str,
        spreadsheet_id: str,
        range_name: str,
        values: List[str]
    ) -> Dict:
        """
        Append a row to a Google Sheets spreadsheet
        
        Args:
            db: Database session
            company_id: Company ID
            spreadsheet_id: Google Sheets spreadsheet ID
            range_name: A1 notation range for where to append (e.g., "Sheet1!A:Z")
            values: List of cell values for the new row
        
        Returns:
            Update response from Sheets API
        """
        try:
            service = await self.get_sheets_service(db, company_id)
            
            body = {
                'values': [values]
            }
            
            result = service.spreadsheets().values().append(
                spreadsheetId=spreadsheet_id,
                range=range_name,
                valueInputOption='USER_ENTERED',
                insertDataOption='INSERT_ROWS',
                body=body
            ).execute()
            
            logger.debug(f"Appended row to spreadsheet {spreadsheet_id}")
            return result
        except HttpError as error:
            logger.error(f"Error writing to spreadsheet {spreadsheet_id}: {error}")
            raise Exception(f"Error writing to spreadsheet: {error}")
    
    async def update_spreadsheet_cell(
        self,
        db: AsyncSession,
        company_id: str,
        spreadsheet_id: str,
        range_name: str,
        value: str
    ) -> Dict:
        """
        Update a single cell or range of cells in a Google Sheets spreadsheet
        
        Args:
            db: Database session
            company_id: Company ID
            spreadsheet_id: Google Sheets spreadsheet ID
            range_name: A1 notation range (e.g., "Sheet1!A2" for single cell, "Sheet1!A2:B2" for range)
            value: Value to set (for range, use nested list)
        
        Returns:
            Update response from Sheets API
        """
        try:
            service = await self.get_sheets_service(db, company_id)
            
            # If value is a string, wrap it in a list for single cell update
            if isinstance(value, str):
                body = {
                    'values': [[value]]
                }
            else:
                body = {
                    'values': value
                }
            
            result = service.spreadsheets().values().update(
                spreadsheetId=spreadsheet_id,
                range=range_name,
                valueInputOption='USER_ENTERED',
                body=body
            ).execute()
            
            logger.debug(f"Updated cell(s) in spreadsheet {spreadsheet_id} at {range_name}")
            return result
        except HttpError as error:
            logger.error(f"Error updating spreadsheet {spreadsheet_id}: {error}")
            raise Exception(f"Error updating spreadsheet: {error}")
    
    async def convert_excel_to_sheets(
        self,
        db: AsyncSession,
        company_id: str,
        excel_file_id: str,
        excel_file_name: str,
        folder_id: Optional[str] = None
    ) -> Dict:
        """
        Convert an Excel file to Google Sheets format
        Checks if a converted version already exists to avoid duplicates
        
        Args:
            db: Database session
            company_id: Company ID
            excel_file_id: Excel file ID in Google Drive
            excel_file_name: Name of the Excel file
            folder_id: Optional folder ID where the Excel file is located
        
        Returns:
            Dict with 'id' and 'name' of the converted Google Sheets file
        """
        try:
            service = await self.get_drive_service(db, company_id)
            
            # Generate the expected name for the converted file (without .xlsx extension)
            converted_name = excel_file_name.replace('.xlsx', '').replace('.XLSX', '').replace('.xls', '').replace('.XLS', '')
            
            # Check if a converted version already exists
            query = f"name='{converted_name}' and mimeType='application/vnd.google-apps.spreadsheet' and trashed=false"
            if folder_id:
                query += f" and '{folder_id}' in parents"
            
            existing_results = service.files().list(
                q=query,
                fields="files(id, name, mimeType)",
                pageSize=1
            ).execute()
            
            existing_files = existing_results.get('files', [])
            if existing_files:
                logger.info(f"Found existing Google Sheets version of '{excel_file_name}': {existing_files[0]['name']} (ID: {existing_files[0]['id']})")
                return {'id': existing_files[0]['id'], 'name': existing_files[0]['name']}
            
            # No existing converted file, create a new one
            # Copy the Excel file and convert it to Google Sheets format
            file_metadata = {
                'name': converted_name,
                'mimeType': 'application/vnd.google-apps.spreadsheet'
            }
            
            # Copy the file with conversion
            converted_file = service.files().copy(
                fileId=excel_file_id,
                body=file_metadata
            ).execute()
            
            logger.info(f"Converted Excel file '{excel_file_name}' to Google Sheets format. New ID: {converted_file['id']}")
            return {'id': converted_file['id'], 'name': converted_file['name']}
        except HttpError as error:
            logger.error(f"Error converting Excel file to Google Sheets: {error}")
            raise Exception(f"Error converting Excel to Google Sheets: {error}")
    
    async def find_spreadsheet_by_name(
        self,
        db: AsyncSession,
        company_id: str,
        spreadsheet_name: str,
        folder_id: Optional[str] = None
    ) -> Optional[Dict]:
        """
        Find a Google Sheets spreadsheet or Excel file by name
        If Excel file is found, it will be converted to Google Sheets format
        
        Args:
            db: Database session
            company_id: Company ID
            spreadsheet_name: Name of the spreadsheet file
            folder_id: Optional folder ID to search within
        
        Returns:
            Dict with 'id' and 'name' if found, None otherwise
        """
        try:
            service = await self.get_drive_service(db, company_id)
            
            # First, try to find Google Sheets format
            query = f"name='{spreadsheet_name}' and mimeType='application/vnd.google-apps.spreadsheet' and trashed=false"
            if folder_id:
                query += f" and '{folder_id}' in parents"
            
            results = service.files().list(
                q=query,
                fields="files(id, name, mimeType)",
                pageSize=10
            ).execute()
            
            files = results.get('files', [])
            if files:
                logger.info(f"Found Google Sheets '{spreadsheet_name}' with ID: {files[0]['id']}")
                return {'id': files[0]['id'], 'name': files[0]['name']}
            
            # If not found, try to find Excel file
            excel_query = f"name='{spreadsheet_name}' and (mimeType='application/vnd.openxmlformats-officedocument.spreadsheetml.sheet' or mimeType='application/vnd.ms-excel') and trashed=false"
            if folder_id:
                excel_query += f" and '{folder_id}' in parents"
            
            excel_results = service.files().list(
                q=excel_query,
                fields="files(id, name, mimeType)",
                pageSize=10
            ).execute()
            
            excel_files = excel_results.get('files', [])
            if excel_files:
                logger.info(f"Found Excel file '{spreadsheet_name}' with ID: {excel_files[0]['id']}. Converting to Google Sheets format...")
                # Convert Excel to Google Sheets
                converted = await self.convert_excel_to_sheets(
                    db, company_id, excel_files[0]['id'], excel_files[0]['name'], folder_id
                )
                return converted
            
            logger.debug(f"Spreadsheet '{spreadsheet_name}' not found")
            return None
        except HttpError as error:
            logger.error(f"Error finding spreadsheet '{spreadsheet_name}': {error}")
            raise Exception(f"Error finding spreadsheet: {error}")


# Singleton instance
google_api_service = GoogleAPIService()

