import os
import pickle
from typing import List, Optional, Tuple
from datetime import datetime
from googleapiclient.discovery import build
from google_auth_oauthlib.flow import InstalledAppFlow
from google.auth.transport.requests import Request
from googleapiclient.errors import HttpError

from app.config import Config
from app.models.document import Document
from app.services.pdf_processor import PDFProcessor
from app.utils.logger import setup_logger


class GoogleDriveService:
    """Service for interacting with Google Drive API"""

    def __init__(self):
        self.logger = setup_logger(__name__)
        self.service = None
        self.pdf_processor = PDFProcessor()
        self._authenticate()

    def _authenticate(self):
        """Authenticate with Google Drive API"""
        creds = None

        # Load existing token
        if os.path.exists(Config.TOKEN_FILE):
            with open(Config.TOKEN_FILE, 'rb') as token:
                creds = pickle.load(token)

        # If no valid credentials, get new ones
        if not creds or not creds.valid:
            if creds and creds.expired and creds.refresh_token:
                creds.refresh(Request())
            else:
                flow = InstalledAppFlow.from_client_secrets_file(
                    Config.CREDENTIALS_FILE, Config.SCOPES)
                creds = flow.run_local_server(port=0)

            # Save credentials for next run
            with open(Config.TOKEN_FILE, 'wb') as token:
                pickle.dump(creds, token)

        self.service = build('drive', 'v3', credentials=creds)
        self.logger.info("Successfully authenticated with Google Drive")

    # def list_pdf_files(self) -> List[dict]:
    #     """List all PDF files in Google Drive"""
    #     try:
    #         query = "mimeType='application/pdf' and trashed=false"
    #         results = self.service.files().list(
    #             q=query,
    #             fields="files(id,name,webViewLink,createdTime,modifiedTime,size,mimeType,parents)"
    #         ).execute()
    #
    #         files = results.get('files', [])
    #         self.logger.info(f"Found {len(files)} PDF files in Google Drive")
    #         return files
    #
    #     except HttpError as e:
    #         self.logger.error(f"Error listing files: {str(e)}")
    #         return []

    def list_pdf_files(self, folder_name: str = None) -> List[dict]:
        """List PDF files in Google Drive, optionally filtered by folder name"""
        try:
            if folder_name:
                self.logger.info(f"Searching for folder: '{folder_name}'")

                # First, find the folder ID by name
                folder_query = f"mimeType='application/vnd.google-apps.folder' and name='{folder_name}' and trashed=false"
                folder_results = self.service.files().list(
                    q=folder_query,
                    fields="files(id,name)"
                ).execute()

                folder_files = folder_results.get('files', [])

                if not folder_files:
                    self.logger.error(f"Folder '{folder_name}' not found!")
                    self.logger.info("Available folders:")

                    # List all folders to help debug
                    all_folders_query = "mimeType='application/vnd.google-apps.folder' and trashed=false"
                    all_folders = self.service.files().list(q=all_folders_query, fields="files(id,name)").execute()
                    for folder in all_folders.get('files', [])[:10]:  # Show first 10 folders
                        self.logger.info(f"  - {folder['name']}")

                    return []

                folder_id = folder_files[0]['id']
                self.logger.info(f"Found folder: '{folder_name}' (ID: {folder_id})")

                # Search for PDFs in this specific folder
                query = f"mimeType='application/pdf' and '{folder_id}' in parents and trashed=false"
            else:
                # Search all PDFs
                query = "mimeType='application/pdf' and trashed=false"

            self.logger.info(f"Using query: {query}")

            results = self.service.files().list(
                q=query,
                fields="files(id,name,webViewLink,createdTime,modifiedTime,size,mimeType,parents)"
            ).execute()

            files = results.get('files', [])
            folder_text = f" in folder '{folder_name}'" if folder_name else ""
            self.logger.info(f"Found {len(files)} PDF files{folder_text}")

            return files

        except HttpError as e:
            self.logger.error(f"Error listing files: {str(e)}")
            return []

    def download_file_content(self, file_id: str) -> Optional[bytes]:
        """Download file content as bytes"""
        try:
            request = self.service.files().get_media(fileId=file_id)
            file_content = request.execute()
            return file_content

        except HttpError as e:
            self.logger.error(f"Error downloading file {file_id}: {str(e)}")
            return None

    def get_file_path(self, file_id: str, parents: List[str]) -> str:
        """Get full path of file including parent folders"""
        try:
            if not parents:
                return "/"

            path_parts = []
            current_parents = parents

            while current_parents:
                parent_id = current_parents[0]
                parent = self.service.files().get(
                    fileId=parent_id,
                    fields="name,parents"
                ).execute()

                path_parts.insert(0, parent.get('name', ''))
                current_parents = parent.get('parents', [])

            return "/" + "/".join(path_parts)

        except HttpError as e:
            self.logger.error(f"Error getting file path: {str(e)}")
            return "/"

    def create_document_from_file(self, file_info: dict) -> Optional[Document]:
        """Create Document object from Google Drive file info"""
        try:
            file_id = file_info['id']

            # Download file content
            file_content = self.download_file_content(file_id)
            if not file_content:
                return None

            # Extract text content
            text_content = self.pdf_processor.extract_text(file_content)
           # text_content = self.pdf_processor.extract_text_with_pages(file_content)
            if not text_content:
                self.logger.warning(f"No text content extracted from {file_info['name']}")
                text_content = ""

            # Get file path
            parents = file_info.get('parents', [])
            file_path = self.get_file_path(file_id, parents)

            # Create document
            document = Document(
                id=file_id,
                name=file_info['name'],
                content=text_content,
                file_path=f"{file_path}/{file_info['name']}",
                web_view_link=file_info['webViewLink'],
                created_time=datetime.fromisoformat(file_info['createdTime'].replace('Z', '+00:00')),
                modified_time=datetime.fromisoformat(file_info['modifiedTime'].replace('Z', '+00:00')),
                size=int(file_info.get('size', 0)),
                mime_type=file_info.get('mimeType')
            )

            return document

        except Exception as e:
            self.logger.error(f"Error creating document from file {file_info.get('name', 'unknown')}: {str(e)}")
            return None

    # def get_all_documents(self) -> List[Document]:
    #     """Get all PDF documents from Google Drive"""
    #     files = self.list_pdf_files()
    #     documents = []
    #
    #     for file_info in files:
    #         document = self.create_document_from_file(file_info)
    #         if document:
    #             documents.append(document)
    #
    #     self.logger.info(f"Successfully processed {len(documents)} documents")
    #     return documents

    def get_all_documents(self) -> List[Document]:
        """Get all PDF documents from Google Drive"""
        from app.config import Config

        # Get folder name from config
        folder_name = getattr(Config, 'GOOGLE_DRIVE_FOLDER', None)

        if folder_name:
            self.logger.info(f"Filtering documents by folder: '{folder_name}'")
        else:
            self.logger.info("Indexing all PDF documents")

        files = self.list_pdf_files(folder_name)
        documents = []

        for file_info in files:
            document = self.create_document_from_file(file_info)
            if document:
                documents.append(document)

        self.logger.info(f"Successfully processed {len(documents)} documents")
        return documents