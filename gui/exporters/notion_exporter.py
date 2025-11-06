"""
Notion exporter for MarkItDown GUI.
"""

import logging
from typing import Dict, Optional, Any
from datetime import datetime
import uuid
import requests

try:
    from notion_client import Client
    HAS_NOTION = True
except ImportError:
    HAS_NOTION = False

from gui.core.exporters import (
    AbstractExporter,
    ExportPlatform,
    ExportResult,
    ExportStatus,
    ExportMapping,
)

logger = logging.getLogger(__name__)


class NotionExporter(AbstractExporter):
    """Notion exporter."""

    def __init__(self) -> None:
        """Initialize Notion exporter."""
        super().__init__(ExportPlatform.NOTION)
        self.client: Optional[Client] = None

    def authenticate(self, credentials: Dict[str, Any]) -> bool:
        """Authenticate with Notion."""
        if not HAS_NOTION:
            logger.error("Notion client not available")
            return False

        try:
            token = credentials.get("notion_token")
            if not token:
                return False

            self.client = Client(auth=token)
            # Verify authentication
            self.client.users.me()
            self.authenticated = True
            logger.info("Notion authenticated")
            return True

        except Exception as e:
            logger.error(f"Notion authentication error: {e}")
            return False

    def export(
        self,
        markdown_text: str,
        metadata: Dict[str, Any],
        destination: Optional[str] = None
    ) -> ExportResult:
        """Export to Notion."""
        if not self.client:
            return ExportResult(
                export_id="",
                platform=ExportPlatform.NOTION,
                status=ExportStatus.FAILED,
                error="Not authenticated"
            )

        try:
            mapped_meta = self._extract_metadata(metadata)
            title = mapped_meta.get("title", "Untitled")

            # Convert markdown to Notion blocks
            blocks = self._markdown_to_notion_blocks(markdown_text)

            # Create page
            parent = {"database_id": destination} if destination else {"type": "workspace"}
            
            response = self.client.pages.create(
                parent=parent,
                properties={
                    "title": {
                        "title": [{"text": {"content": title}}]
                    }
                },
                children=blocks
            )

            page_id = response.get("id")
            page_url = response.get("url", "")

            return ExportResult(
                export_id=str(uuid.uuid4()),
                platform=ExportPlatform.NOTION,
                status=ExportStatus.COMPLETED,
                exported_id=page_id,
                exported_url=page_url,
                metadata={"page_id": page_id}
            )

        except Exception as e:
            logger.error(f"Notion export error: {e}")
            return ExportResult(
                export_id="",
                platform=ExportPlatform.NOTION,
                status=ExportStatus.FAILED,
                error=str(e)
            )

    def _markdown_to_notion_blocks(self, markdown_text: str) -> list:
        """Convert Markdown to Notion blocks."""
        blocks = []
        lines = markdown_text.split("\n")

        for line in lines:
            line = line.strip()
            if not line:
                continue

            if line.startswith("# "):
                blocks.append({
                    "object": "block",
                    "type": "heading_1",
                    "heading_1": {
                        "rich_text": [{"type": "text", "text": {"content": line[2:]}}]
                    }
                })
            elif line.startswith("## "):
                blocks.append({
                    "object": "block",
                    "type": "heading_2",
                    "heading_2": {
                        "rich_text": [{"type": "text", "text": {"content": line[3:]}}]
                    }
                })
            elif line.startswith("### "):
                blocks.append({
                    "object": "block",
                    "type": "heading_3",
                    "heading_3": {
                        "rich_text": [{"type": "text", "text": {"content": line[4:]}}]
                    }
                })
            elif line.startswith("- ") or line.startswith("* "):
                blocks.append({
                    "object": "block",
                    "type": "bulleted_list_item",
                    "bulleted_list_item": {
                        "rich_text": [{"type": "text", "text": {"content": line[2:]}}]
                    }
                })
            elif line.startswith("```"):
                # Code block (simplified)
                continue
            else:
                blocks.append({
                    "object": "block",
                    "type": "paragraph",
                    "paragraph": {
                        "rich_text": [{"type": "text", "text": {"content": line}}]
                    }
                })

        return blocks

    def get_export_url(self, export_id: str) -> Optional[str]:
        """Get URL for exported content."""
        if not self.client:
            return None

        try:
            page = self.client.pages.retrieve(export_id)
            return page.get("url")
        except Exception as e:
            logger.error(f"Error getting Notion URL: {e}")
            return None



