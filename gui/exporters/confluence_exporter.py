"""
Confluence exporter for MarkItDown GUI.
"""

import logging
from typing import Dict, Optional, Any
from datetime import datetime
import uuid
import requests
from requests.auth import HTTPBasicAuth

try:
    from markdown import markdown
    HAS_MARKDOWN = True
except ImportError:
    HAS_MARKDOWN = False

from gui.core.exporters import (
    AbstractExporter,
    ExportPlatform,
    ExportResult,
    ExportStatus,
)

logger = logging.getLogger(__name__)


class ConfluenceExporter(AbstractExporter):
    """Confluence exporter."""

    def __init__(self) -> None:
        """Initialize Confluence exporter."""
        super().__init__(ExportPlatform.CONFLUENCE)
        self.base_url: Optional[str] = None
        self.session = None

    def authenticate(self, credentials: Dict[str, Any]) -> bool:
        """Authenticate with Confluence."""
        try:
            self.base_url = credentials.get("base_url", "").rstrip("/")
            username = credentials.get("username")
            api_token = credentials.get("api_token")

            if not self.base_url or not username or not api_token:
                return False

            # Test authentication
            auth = HTTPBasicAuth(username, api_token)
            response = requests.get(
                f"{self.base_url}/rest/api/user/current",
                auth=auth
            )

            if response.status_code == 200:
                self.session = requests.Session()
                self.session.auth = auth
                self.authenticated = True
                logger.info("Confluence authenticated")
                return True

            return False

        except Exception as e:
            logger.error(f"Confluence authentication error: {e}")
            return False

    def export(
        self,
        markdown_text: str,
        metadata: Dict[str, Any],
        destination: Optional[str] = None
    ) -> ExportResult:
        """Export to Confluence."""
        if not self.session or not self.base_url:
            return ExportResult(
                export_id="",
                platform=ExportPlatform.CONFLUENCE,
                status=ExportStatus.FAILED,
                error="Not authenticated"
            )

        try:
            if not HAS_MARKDOWN:
                return ExportResult(
                    export_id="",
                    platform=ExportPlatform.CONFLUENCE,
                    status=ExportStatus.FAILED,
                    error="markdown library not available"
                )

            mapped_meta = self._extract_metadata(metadata)
            title = mapped_meta.get("title", "Untitled")

            # Convert markdown to HTML
            html_content = markdown(markdown_text)

            # Parse destination (space_key:page_title or page_id)
            space_key = destination or metadata.get("space_key", "~")
            page_id = None
            if ":" in space_key:
                space_key, page_title = space_key.split(":", 1)
            else:
                page_title = title

            # Create or update page
            if page_id:
                # Update existing page
                url = f"{self.base_url}/rest/api/content/{page_id}"
                data = {
                    "version": {"number": metadata.get("version", 1) + 1},
                    "title": title,
                    "type": "page",
                    "body": {
                        "storage": {
                            "value": html_content,
                            "representation": "storage"
                        }
                    }
                }
                response = self.session.put(url, json=data)
            else:
                # Create new page
                url = f"{self.base_url}/rest/api/content"
                data = {
                    "type": "page",
                    "title": title,
                    "space": {"key": space_key},
                    "body": {
                        "storage": {
                            "value": html_content,
                            "representation": "storage"
                        }
                    }
                }
                response = self.session.post(url, json=data)

            response.raise_for_status()
            result_data = response.json()
            page_id = result_data.get("id")
            page_url = result_data.get("_links", {}).get("webui", "")

            return ExportResult(
                export_id=str(uuid.uuid4()),
                platform=ExportPlatform.CONFLUENCE,
                status=ExportStatus.COMPLETED,
                exported_id=page_id,
                exported_url=f"{self.base_url}{page_url}" if page_url else None,
                metadata={"page_id": page_id, "space_key": space_key}
            )

        except Exception as e:
            logger.error(f"Confluence export error: {e}")
            return ExportResult(
                export_id="",
                platform=ExportPlatform.CONFLUENCE,
                status=ExportStatus.FAILED,
                error=str(e)
            )

    def get_export_url(self, export_id: str) -> Optional[str]:
        """Get URL for exported content."""
        if not self.base_url:
            return None

        try:
            url = f"{self.base_url}/rest/api/content/{export_id}"
            response = self.session.get(url)
            if response.status_code == 200:
                data = response.json()
                webui = data.get("_links", {}).get("webui", "")
                return f"{self.base_url}{webui}" if webui else None
        except Exception as e:
            logger.error(f"Error getting Confluence URL: {e}")
        return None

