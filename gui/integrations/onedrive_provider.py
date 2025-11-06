"""
OneDrive integration for MarkItDown GUI.
"""

import logging
from pathlib import Path
from typing import List, Dict, Optional, Any
from datetime import datetime
import requests

try:
    import msal
    HAS_ONEDRIVE = True
except ImportError:
    HAS_ONEDRIVE = False

from gui.core.cloud_storage import (
    CloudStorageProvider,
    CloudProvider,
    CloudFile,
)

logger = logging.getLogger(__name__)

GRAPH_API_ENDPOINT = "https://graph.microsoft.com/v1.0"


class OneDriveProvider(CloudStorageProvider):
    """OneDrive storage provider."""

    def __init__(self) -> None:
        """Initialize OneDrive provider."""
        super().__init__(CloudProvider.ONEDRIVE)
        self.app: Optional[msal.PublicClientApplication] = None
        self.access_token: Optional[str] = None

    def authenticate(self, credentials: Dict[str, Any]) -> bool:
        """Authenticate with OneDrive."""
        if not HAS_ONEDRIVE:
            logger.error("MSAL not available")
            return False

        try:
            client_id = credentials.get("client_id")
            if not client_id:
                return False

            self.app = msal.PublicClientApplication(
                client_id,
                authority="https://login.microsoftonline.com/common"
            )

            # Try to get token from cache
            accounts = self.app.get_accounts()
            if accounts:
                result = self.app.acquire_token_silent(
                    ["Files.ReadWrite"],
                    account=accounts[0]
                )
            else:
                # Interactive login
                result = self.app.acquire_token_interactive(
                    ["Files.ReadWrite"]
                )

            if "access_token" in result:
                self.access_token = result["access_token"]
                self.authenticated = True
                logger.info("OneDrive authenticated")
                return True
            else:
                logger.error(f"OneDrive authentication failed: {result.get('error_description')}")
                return False

        except Exception as e:
            logger.error(f"OneDrive authentication error: {e}")
            return False

    def _make_request(self, method: str, endpoint: str, **kwargs) -> Optional[Dict]:
        """Make API request to Microsoft Graph."""
        if not self.access_token:
            return None

        headers = {"Authorization": f"Bearer {self.access_token}"}
        url = f"{GRAPH_API_ENDPOINT}{endpoint}"

        try:
            response = requests.request(method, url, headers=headers, **kwargs)
            response.raise_for_status()
            return response.json()
        except Exception as e:
            logger.error(f"OneDrive API error: {e}")
            return None

    def list_files(self, folder_id: Optional[str] = None) -> List[CloudFile]:
        """List files in OneDrive."""
        if not self.access_token:
            return []

        endpoint = f"/me/drive/items/{folder_id}/children" if folder_id else "/me/drive/root/children"
        result = self._make_request("GET", endpoint)

        if not result:
            return []

        files = []
        for item in result.get('value', []):
            modified_time = datetime.fromisoformat(
                item.get('lastModifiedDateTime', '').replace('Z', '+00:00')
            ) if item.get('lastModifiedDateTime') else datetime.now()

            is_folder = 'folder' in item

            files.append(CloudFile(
                file_id=item['id'],
                name=item['name'],
                path=item.get('webUrl', ''),
                size=item.get('size', 0),
                modified_time=modified_time,
                is_folder=is_folder,
                mime_type=item.get('file', {}).get('mimeType'),
                provider=CloudProvider.ONEDRIVE,
                parent_id=item.get('parentReference', {}).get('id'),
                share_url=item.get('webUrl'),
            ))

        return files

    def download_file(self, file_id: str, local_path: Path) -> bool:
        """Download file from OneDrive."""
        if not self.access_token:
            return False

        endpoint = f"/me/drive/items/{file_id}/content"
        url = f"{GRAPH_API_ENDPOINT}{endpoint}"
        headers = {"Authorization": f"Bearer {self.access_token}"}

        try:
            response = requests.get(url, headers=headers, stream=True)
            response.raise_for_status()
            local_path.parent.mkdir(parents=True, exist_ok=True)
            with open(local_path, 'wb') as f:
                for chunk in response.iter_content(chunk_size=8192):
                    f.write(chunk)
            return True
        except Exception as e:
            logger.error(f"Error downloading from OneDrive: {e}")
            return False

    def upload_file(self, local_path: Path, cloud_path: str, folder_id: Optional[str] = None) -> Optional[str]:
        """Upload file to OneDrive."""
        if not self.access_token:
            return None

        endpoint = f"/me/drive/items/{folder_id}:/{cloud_path}:/content" if folder_id else f"/me/drive/root:/{cloud_path}:/content"
        url = f"{GRAPH_API_ENDPOINT}{endpoint}"
        headers = {"Authorization": f"Bearer {self.access_token}"}

        try:
            with open(local_path, 'rb') as f:
                response = requests.put(url, headers=headers, data=f)
                response.raise_for_status()
                result = response.json()
                return result.get('id')
        except Exception as e:
            logger.error(f"Error uploading to OneDrive: {e}")
            return None

    def delete_file(self, file_id: str) -> bool:
        """Delete file from OneDrive."""
        if not self.access_token:
            return False

        endpoint = f"/me/drive/items/{file_id}"
        result = self._make_request("DELETE", endpoint)
        return result is not None

    def get_share_link(self, file_id: str) -> Optional[str]:
        """Get shareable link for file."""
        if not self.access_token:
            return None

        endpoint = f"/me/drive/items/{file_id}/createLink"
        data = {"type": "view", "scope": "anonymous"}
        result = self._make_request("POST", endpoint, json=data)

        if result:
            return result.get('link', {}).get('webUrl')
        return None

    def create_folder(self, name: str, parent_id: Optional[str] = None) -> Optional[str]:
        """Create folder in OneDrive."""
        if not self.access_token:
            return None

        endpoint = f"/me/drive/items/{parent_id}/children" if parent_id else "/me/drive/root/children"
        data = {
            "name": name,
            "folder": {},
            "@microsoft.graph.conflictBehavior": "rename"
        }
        result = self._make_request("POST", endpoint, json=data)

        if result:
            return result.get('id')
        return None

