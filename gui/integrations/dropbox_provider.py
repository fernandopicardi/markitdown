"""
Dropbox integration for MarkItDown GUI.
"""

import logging
from pathlib import Path
from typing import List, Dict, Optional, Any
from datetime import datetime

try:
    import dropbox
    from dropbox.exceptions import ApiError, AuthError
    HAS_DROPBOX = True
except ImportError:
    HAS_DROPBOX = False

from gui.core.cloud_storage import (
    CloudStorageProvider,
    CloudProvider,
    CloudFile,
)

logger = logging.getLogger(__name__)


class DropboxProvider(CloudStorageProvider):
    """Dropbox storage provider."""

    def __init__(self) -> None:
        """Initialize Dropbox provider."""
        super().__init__(CloudProvider.DROPBOX)
        self.client: Optional[dropbox.Dropbox] = None

    def authenticate(self, credentials: Dict[str, Any]) -> bool:
        """Authenticate with Dropbox."""
        if not HAS_DROPBOX:
            logger.error("Dropbox SDK not available")
            return False

        try:
            access_token = credentials.get("access_token")
            if not access_token:
                return False

            self.client = dropbox.Dropbox(access_token)
            # Verify authentication
            self.client.users_get_current_account()
            self.authenticated = True
            logger.info("Dropbox authenticated")
            return True

        except AuthError as e:
            logger.error(f"Dropbox authentication error: {e}")
            return False
        except Exception as e:
            logger.error(f"Dropbox error: {e}")
            return False

    def list_files(self, folder_id: Optional[str] = None) -> List[CloudFile]:
        """List files in Dropbox."""
        if not self.client:
            return []

        try:
            path = folder_id if folder_id else ""
            result = self.client.files_list_folder(path)

            files = []
            for entry in result.entries:
                if isinstance(entry, dropbox.files.FileMetadata):
                    modified_time = entry.server_modified
                    files.append(CloudFile(
                        file_id=entry.id,
                        name=entry.name,
                        path=entry.path_display,
                        size=entry.size,
                        modified_time=modified_time,
                        is_folder=False,
                        mime_type=None,
                        provider=CloudProvider.DROPBOX,
                        parent_id=entry.path_display.rsplit('/', 1)[0] if '/' in entry.path_display else None,
                    ))
                elif isinstance(entry, dropbox.files.FolderMetadata):
                    files.append(CloudFile(
                        file_id=entry.id,
                        name=entry.name,
                        path=entry.path_display,
                        size=0,
                        modified_time=datetime.now(),
                        is_folder=True,
                        provider=CloudProvider.DROPBOX,
                        parent_id=entry.path_display.rsplit('/', 1)[0] if '/' in entry.path_display else None,
                    ))

            return files

        except ApiError as e:
            logger.error(f"Error listing Dropbox files: {e}")
            return []

    def download_file(self, file_id: str, local_path: Path) -> bool:
        """Download file from Dropbox."""
        if not self.client:
            return False

        try:
            # Dropbox uses path, not file_id
            metadata, response = self.client.files_download(file_id)
            local_path.parent.mkdir(parents=True, exist_ok=True)
            with open(local_path, 'wb') as f:
                f.write(response.content)
            return True

        except ApiError as e:
            logger.error(f"Error downloading from Dropbox: {e}")
            return False

    def upload_file(self, local_path: Path, cloud_path: str, folder_id: Optional[str] = None) -> Optional[str]:
        """Upload file to Dropbox."""
        if not self.client:
            return None

        try:
            full_path = f"{folder_id}/{cloud_path}" if folder_id else cloud_path
            with open(local_path, 'rb') as f:
                metadata = self.client.files_upload(
                    f.read(),
                    full_path,
                    mode=dropbox.files.WriteMode.overwrite
                )
            return metadata.id

        except ApiError as e:
            logger.error(f"Error uploading to Dropbox: {e}")
            return None

    def delete_file(self, file_id: str) -> bool:
        """Delete file from Dropbox."""
        if not self.client:
            return False

        try:
            self.client.files_delete_v2(file_id)
            return True
        except ApiError as e:
            logger.error(f"Error deleting from Dropbox: {e}")
            return False

    def get_share_link(self, file_id: str) -> Optional[str]:
        """Get shareable link for file."""
        if not self.client:
            return None

        try:
            link = self.client.sharing_create_shared_link_with_settings(file_id)
            return link.url
        except ApiError as e:
            logger.error(f"Error getting share link: {e}")
            return None

    def create_folder(self, name: str, parent_id: Optional[str] = None) -> Optional[str]:
        """Create folder in Dropbox."""
        if not self.client:
            return None

        try:
            full_path = f"{parent_id}/{name}" if parent_id else f"/{name}"
            metadata = self.client.files_create_folder_v2(full_path)
            return metadata.metadata.id
        except ApiError as e:
            logger.error(f"Error creating folder: {e}")
            return None

