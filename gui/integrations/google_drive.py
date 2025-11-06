"""
Google Drive integration for MarkItDown GUI.
"""

import logging
from pathlib import Path
from typing import List, Dict, Optional, Any
from datetime import datetime

try:
    from google.oauth2.credentials import Credentials
    from google_auth_oauthlib.flow import InstalledAppFlow
    from googleapiclient.discovery import build
    from googleapiclient.http import MediaFileUpload, MediaIoBaseDownload
    from googleapiclient.errors import HttpError
    import io
    HAS_GOOGLE = True
except ImportError:
    HAS_GOOGLE = False

from gui.core.cloud_storage import (
    CloudStorageProvider,
    CloudProvider,
    CloudFile,
)

logger = logging.getLogger(__name__)

SCOPES = ['https://www.googleapis.com/auth/drive.file']


class GoogleDriveProvider(CloudStorageProvider):
    """Google Drive storage provider."""

    def __init__(self) -> None:
        """Initialize Google Drive provider."""
        super().__init__(CloudProvider.GOOGLE_DRIVE)
        self.service = None
        self.credentials: Optional[Credentials] = None

    def authenticate(self, credentials: Dict[str, Any]) -> bool:
        """Authenticate with Google Drive."""
        if not HAS_GOOGLE:
            logger.error("Google API client not available")
            return False

        try:
            # Check for existing token
            token_path = self.cache_dir / "google_token.json" if self.cache_dir else None
            if token_path and token_path.exists():
                self.credentials = Credentials.from_authorized_user_file(str(token_path), SCOPES)

            # If no valid credentials, do OAuth flow
            if not self.credentials or not self.credentials.valid:
                if self.credentials and self.credentials.expired and self.credentials.refresh_token:
                    from google.auth.transport.requests import Request
                    self.credentials.refresh(Request())
                else:
                    client_config = credentials.get("client_config")
                    if not client_config:
                        return False

                    flow = InstalledAppFlow.from_client_config(client_config, SCOPES)
                    self.credentials = flow.run_local_server(port=0)

                    # Save credentials
                    if token_path:
                        with open(token_path, 'w') as token:
                            token.write(self.credentials.to_json())

            # Build service
            self.service = build('drive', 'v3', credentials=self.credentials)
            self.authenticated = True
            logger.info("Google Drive authenticated")
            return True

        except Exception as e:
            logger.error(f"Google Drive authentication error: {e}")
            return False

    def list_files(self, folder_id: Optional[str] = None) -> List[CloudFile]:
        """List files in Google Drive."""
        if not self.service:
            return []

        try:
            query = "trashed=false"
            if folder_id:
                query += f" and '{folder_id}' in parents"
            else:
                query += " and 'root' in parents"

            results = self.service.files().list(
                q=query,
                fields="files(id, name, mimeType, size, modifiedTime, parents, webViewLink)"
            ).execute()

            files = []
            for item in results.get('files', []):
                modified_time = datetime.fromisoformat(
                    item.get('modifiedTime', '').replace('Z', '+00:00')
                ) if item.get('modifiedTime') else datetime.now()

                is_folder = item.get('mimeType') == 'application/vnd.google-apps.folder'

                files.append(CloudFile(
                    file_id=item['id'],
                    name=item['name'],
                    path=item['name'],
                    size=int(item.get('size', 0)),
                    modified_time=modified_time,
                    is_folder=is_folder,
                    mime_type=item.get('mimeType'),
                    provider=CloudProvider.GOOGLE_DRIVE,
                    parent_id=item.get('parents', [None])[0] if item.get('parents') else None,
                    share_url=item.get('webViewLink'),
                ))

            return files

        except HttpError as e:
            logger.error(f"Error listing Google Drive files: {e}")
            return []

    def download_file(self, file_id: str, local_path: Path) -> bool:
        """Download file from Google Drive."""
        if not self.service:
            return False

        try:
            request = self.service.files().get_media(fileId=file_id)
            fh = io.BytesIO()
            downloader = MediaIoBaseDownload(fh, request)

            done = False
            while not done:
                status, done = downloader.next_chunk()

            local_path.parent.mkdir(parents=True, exist_ok=True)
            with open(local_path, 'wb') as f:
                f.write(fh.getvalue())

            return True

        except HttpError as e:
            logger.error(f"Error downloading from Google Drive: {e}")
            return False

    def upload_file(self, local_path: Path, cloud_path: str, folder_id: Optional[str] = None) -> Optional[str]:
        """Upload file to Google Drive."""
        if not self.service:
            return None

        try:
            file_metadata = {'name': cloud_path}
            if folder_id:
                file_metadata['parents'] = [folder_id]

            media = MediaFileUpload(str(local_path), resumable=True)
            file = self.service.files().create(
                body=file_metadata,
                media_body=media,
                fields='id'
            ).execute()

            return file.get('id')

        except HttpError as e:
            logger.error(f"Error uploading to Google Drive: {e}")
            return None

    def delete_file(self, file_id: str) -> bool:
        """Delete file from Google Drive."""
        if not self.service:
            return False

        try:
            self.service.files().delete(fileId=file_id).execute()
            return True
        except HttpError as e:
            logger.error(f"Error deleting from Google Drive: {e}")
            return False

    def get_share_link(self, file_id: str) -> Optional[str]:
        """Get shareable link for file."""
        if not self.service:
            return None

        try:
            file = self.service.files().get(
                fileId=file_id,
                fields='webViewLink'
            ).execute()
            return file.get('webViewLink')
        except HttpError as e:
            logger.error(f"Error getting share link: {e}")
            return None

    def create_folder(self, name: str, parent_id: Optional[str] = None) -> Optional[str]:
        """Create folder in Google Drive."""
        if not self.service:
            return None

        try:
            file_metadata = {
                'name': name,
                'mimeType': 'application/vnd.google-apps.folder'
            }
            if parent_id:
                file_metadata['parents'] = [parent_id]

            file = self.service.files().create(
                body=file_metadata,
                fields='id'
            ).execute()

            return file.get('id')
        except HttpError as e:
            logger.error(f"Error creating folder: {e}")
            return None

