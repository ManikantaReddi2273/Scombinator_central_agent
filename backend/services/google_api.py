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


# Singleton instance
google_api_service = GoogleAPIService()

