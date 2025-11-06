"""
Notion Export Plugin for MarkItDown GUI.

This plugin provides export functionality to Notion.
"""

from pathlib import Path
from typing import Dict, Any, Optional
import logging

try:
    from notion_client import Client
    HAS_NOTION = True
except ImportError:
    HAS_NOTION = False

from gui.core.plugin_system import (
    AbstractPlugin,
    PluginMetadata,
    PluginType,
    PluginStatus,
)

logger = logging.getLogger(__name__)

PLUGIN_METADATA = PluginMetadata(
    plugin_id="notion_export",
    name="Notion Export",
    version="1.0.0",
    description="Export converted Markdown to Notion pages",
    author="MarkItDown Team",
    plugin_type=PluginType.INTEGRATION,
    dependencies=[],
    config_schema={
        "notion_token": {"type": "string", "default": "", "secret": True},
        "default_database_id": {"type": "string", "default": ""},
    },
    permissions=["network_access", "notion_write"],
)


class NotionPlugin(AbstractPlugin):
    """Notion export plugin."""

    def __init__(self, plugin_id: str, metadata: PluginMetadata) -> None:
        """Initialize Notion plugin."""
        super().__init__(plugin_id, metadata)
        self.notion_client: Optional[Client] = None
        self.notion_available = HAS_NOTION

    def init(self, context: Dict[str, Any]) -> None:
        """Initialize plugin."""
        notion_token = self.config.get("notion_token", "")
        if notion_token and self.notion_available:
            try:
                self.notion_client = Client(auth=notion_token)
                self.logger.info("Notion client initialized")
            except Exception as e:
                self.logger.error(f"Failed to initialize Notion client: {e}")

    def activate(self) -> None:
        """Activate plugin."""
        if not self.notion_available:
            raise RuntimeError("Notion client not available")

        notion_token = self.config.get("notion_token", "")
        if not notion_token:
            raise RuntimeError("Notion token not configured")

        try:
            self.notion_client = Client(auth=notion_token)
            self.status = PluginStatus.ACTIVATED
            self.logger.info("Notion plugin activated")
        except Exception as e:
            self.logger.error(f"Error activating Notion plugin: {e}")
            raise

    def deactivate(self) -> None:
        """Deactivate plugin."""
        self.notion_client = None
        self.status = PluginStatus.DEACTIVATED
        self.logger.info("Notion plugin deactivated")

    def export_to_notion(
        self,
        markdown_text: str,
        title: str,
        database_id: Optional[str] = None
    ) -> Optional[str]:
        """
        Export Markdown to Notion page.
        
        Args:
            markdown_text: Markdown text to export
            title: Page title
            database_id: Notion database ID (uses default if None)
            
        Returns:
            Created page ID or None
        """
        if not self.notion_client:
            self.logger.error("Notion client not initialized")
            return None

        try:
            db_id = database_id or self.config.get("default_database_id", "")
            if not db_id:
                self.logger.error("No database ID provided")
                return None

            # Convert markdown to Notion blocks (simplified)
            blocks = self._markdown_to_notion_blocks(markdown_text)

            # Create page
            response = self.notion_client.pages.create(
                parent={"database_id": db_id},
                properties={
                    "title": {
                        "title": [{"text": {"content": title}}]
                    }
                },
                children=blocks
            )

            page_id = response.get("id")
            self.logger.info(f"Exported to Notion: {page_id}")
            return page_id

        except Exception as e:
            self.logger.error(f"Error exporting to Notion: {e}")
            return None

    def _markdown_to_notion_blocks(self, markdown_text: str) -> list:
        """
        Convert Markdown to Notion blocks.
        
        Args:
            markdown_text: Markdown text
            
        Returns:
            List of Notion blocks
        """
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
            elif line.startswith("- ") or line.startswith("* "):
                blocks.append({
                    "object": "block",
                    "type": "bulleted_list_item",
                    "bulleted_list_item": {
                        "rich_text": [{"type": "text", "text": {"content": line[2:]}}]
                    }
                })
            else:
                blocks.append({
                    "object": "block",
                    "type": "paragraph",
                    "paragraph": {
                        "rich_text": [{"type": "text", "text": {"content": line}}]
                    }
                })

        return blocks

