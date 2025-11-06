"""
WordPress exporter for MarkItDown GUI.
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


class WordPressExporter(AbstractExporter):
    """WordPress exporter."""

    def __init__(self) -> None:
        """Initialize WordPress exporter."""
        super().__init__(ExportPlatform.WORDPRESS)
        self.base_url: Optional[str] = None
        self.username: Optional[str] = None
        self.password: Optional[str] = None
        self.session = None

    def authenticate(self, credentials: Dict[str, Any]) -> bool:
        """Authenticate with WordPress."""
        if not HAS_REQUESTS:
            logger.error("requests not available")
            return False

        try:
            self.base_url = credentials.get("base_url", "").rstrip("/")
            self.username = credentials.get("username")
            self.password = credentials.get("password") or credentials.get("application_password")

            if not self.base_url or not self.username or not self.password:
                return False

            # Test authentication
            import requests
            from requests.auth import HTTPBasicAuth

            auth = HTTPBasicAuth(self.username, self.password)
            response = requests.get(
                f"{self.base_url}/wp-json/wp/v2/users/me",
                auth=auth
            )

            if response.status_code == 200:
                self.session = requests.Session()
                self.session.auth = auth
                self.authenticated = True
                logger.info("WordPress authenticated")
                return True

            return False

        except Exception as e:
            logger.error(f"WordPress authentication error: {e}")
            return False

    def export(
        self,
        markdown_text: str,
        metadata: Dict[str, Any],
        destination: Optional[str] = None
    ) -> ExportResult:
        """Export to WordPress."""
        if not self.session or not self.base_url:
            return ExportResult(
                export_id="",
                platform=ExportPlatform.WORDPRESS,
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
                    platform=ExportPlatform.WORDPRESS,
                    status=ExportStatus.FAILED,
                    error="markdown library not available"
                )

            mapped_meta = self._extract_metadata(metadata)
            title = mapped_meta.get("title", "Untitled")

            # Convert markdown to HTML
            html_content = markdown(markdown_text)

            # Prepare post data
            post_type = "page" if destination == "page" else "post"
            post_data = {
                "title": title,
                "content": html_content,
                "status": metadata.get("status", "draft"),
                "type": post_type,
            }

            # Add categories
            if mapped_meta.get("categories"):
                post_data["categories"] = mapped_meta["categories"]

            # Add tags
            if mapped_meta.get("tags"):
                post_data["tags"] = mapped_meta["tags"]

            # Featured image
            if metadata.get("featured_image_id"):
                post_data["featured_media"] = metadata["featured_image_id"]

            # Create or update post
            if metadata.get("post_id"):
                # Update existing
                url = f"{self.base_url}/wp-json/wp/v2/{post_type}s/{metadata['post_id']}"
                response = self.session.post(url, json=post_data)
            else:
                # Create new
                url = f"{self.base_url}/wp-json/wp/v2/{post_type}s"
                response = self.session.post(url, json=post_data)

            response.raise_for_status()
            result_data = response.json()
            post_id = result_data.get("id")
            post_url = result_data.get("link")

            return ExportResult(
                export_id=str(uuid.uuid4()),
                platform=ExportPlatform.WORDPRESS,
                status=ExportStatus.COMPLETED,
                exported_id=str(post_id),
                exported_url=post_url,
                metadata={"post_id": post_id, "type": post_type}
            )

        except Exception as e:
            logger.error(f"WordPress export error: {e}")
            return ExportResult(
                export_id="",
                platform=ExportPlatform.WORDPRESS,
                status=ExportStatus.FAILED,
                error=str(e)
            )

    def get_export_url(self, export_id: str) -> Optional[str]:
        """Get URL for exported content."""
        if not self.base_url or not self.session:
            return None

        try:
            url = f"{self.base_url}/wp-json/wp/v2/posts/{export_id}"
            response = self.session.get(url)
            if response.status_code == 200:
                data = response.json()
                return data.get("link")
        except Exception as e:
            logger.error(f"Error getting WordPress URL: {e}")
        return None

