"""
Medium exporter for MarkItDown GUI.
"""

import logging
from typing import Dict, Optional, Any
from datetime import datetime
import uuid

try:
    import requests
    HAS_REQUESTS = True
except ImportError:
    HAS_REQUESTS = False

from gui.core.exporters import (
    AbstractExporter,
    ExportPlatform,
    ExportResult,
    ExportStatus,
)

logger = logging.getLogger(__name__)


class MediumExporter(AbstractExporter):
    """Medium exporter."""

    def __init__(self) -> None:
        """Initialize Medium exporter."""
        super().__init__(ExportPlatform.MEDIUM)
        self.access_token: Optional[str] = None
        self.user_id: Optional[str] = None

    def authenticate(self, credentials: Dict[str, Any]) -> bool:
        """Authenticate with Medium."""
        if not HAS_REQUESTS:
            logger.error("requests not available")
            return False

        try:
            self.access_token = credentials.get("access_token")
            if not self.access_token:
                return False

            # Get user info
            headers = {
                "Authorization": f"Bearer {self.access_token}",
                "Content-Type": "application/json"
            }
            response = requests.get("https://api.medium.com/v1/me", headers=headers)

            if response.status_code == 200:
                data = response.json()
                self.user_id = data.get("data", {}).get("id")
                self.authenticated = True
                logger.info("Medium authenticated")
                return True

            return False

        except Exception as e:
            logger.error(f"Medium authentication error: {e}")
            return False

    def export(
        self,
        markdown_text: str,
        metadata: Dict[str, Any],
        destination: Optional[str] = None
    ) -> ExportResult:
        """Export to Medium."""
        if not self.access_token or not self.user_id:
            return ExportResult(
                export_id="",
                platform=ExportPlatform.MEDIUM,
                status=ExportStatus.FAILED,
                error="Not authenticated"
            )

        try:
            try:
                from markdown import markdown
                HAS_MARKDOWN = True
            except ImportError:
                HAS_MARKDOWN = False

            if not HAS_MARKDOWN:
                return ExportResult(
                    export_id="",
                    platform=ExportPlatform.MEDIUM,
                    status=ExportStatus.FAILED,
                    error="markdown library not available"
                )

            mapped_meta = self._extract_metadata(metadata)
            title = mapped_meta.get("title", "Untitled")

            # Convert markdown to HTML
            html_content = markdown(markdown_text)

            # Prepare post data
            post_data = {
                "title": title,
                "contentFormat": "html",
                "content": html_content,
                "tags": mapped_meta.get("tags", []),
                "publishStatus": metadata.get("status", "draft"),  # draft or public
            }

            # Create post
            headers = {
                "Authorization": f"Bearer {self.access_token}",
                "Content-Type": "application/json"
            }
            url = f"https://api.medium.com/v1/users/{self.user_id}/posts"
            response = requests.post(url, json=post_data, headers=headers)

            response.raise_for_status()
            result_data = response.json()
            post_data = result_data.get("data", {})
            post_id = post_data.get("id")
            post_url = post_data.get("url")

            return ExportResult(
                export_id=str(uuid.uuid4()),
                platform=ExportPlatform.MEDIUM,
                status=ExportStatus.COMPLETED,
                exported_id=post_id,
                exported_url=post_url,
                metadata={"post_id": post_id}
            )

        except Exception as e:
            logger.error(f"Medium export error: {e}")
            return ExportResult(
                export_id="",
                platform=ExportPlatform.MEDIUM,
                status=ExportStatus.FAILED,
                error=str(e)
            )

    def get_export_url(self, export_id: str) -> Optional[str]:
        """Get URL for exported content."""
        # Medium API doesn't provide direct URL retrieval
        # URL is returned in export response
        return None

