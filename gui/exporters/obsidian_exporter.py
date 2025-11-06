"""
Obsidian exporter for MarkItDown GUI.
"""

import logging
from pathlib import Path
from typing import Dict, Optional, Any
from datetime import datetime
import uuid
import re

try:
    import yaml
    HAS_YAML = True
except ImportError:
    HAS_YAML = False

from gui.core.exporters import (
    AbstractExporter,
    ExportPlatform,
    ExportResult,
    ExportStatus,
)

logger = logging.getLogger(__name__)


class ObsidianExporter(AbstractExporter):
    """Obsidian exporter."""

    def __init__(self) -> None:
        """Initialize Obsidian exporter."""
        super().__init__(ExportPlatform.OBSIDIAN)
        self.vault_path: Optional[Path] = None

    def authenticate(self, credentials: Dict[str, Any]) -> bool:
        """Authenticate with Obsidian vault."""
        try:
            vault_path = Path(credentials.get("vault_path", ""))
            if not vault_path or not vault_path.exists():
                return False

            # Verify it's an Obsidian vault (has .obsidian folder)
            if not (vault_path / ".obsidian").exists():
                logger.warning("Path doesn't appear to be an Obsidian vault")
                # Continue anyway

            self.vault_path = vault_path
            self.authenticated = True
            logger.info("Obsidian vault authenticated")
            return True

        except Exception as e:
            logger.error(f"Obsidian authentication error: {e}")
            return False

    def export(
        self,
        markdown_text: str,
        metadata: Dict[str, Any],
        destination: Optional[str] = None
    ) -> ExportResult:
        """Export to Obsidian."""
        if not self.vault_path:
            return ExportResult(
                export_id="",
                platform=ExportPlatform.OBSIDIAN,
                status=ExportStatus.FAILED,
                error="Not authenticated"
            )

        try:
            mapped_meta = self._extract_metadata(metadata)
            title = mapped_meta.get("title", "Untitled")

            # Generate filename
            filename = destination or self._title_to_filename(title) + ".md"
            file_path = self.vault_path / filename

            # Create frontmatter
            frontmatter = {
                "title": title,
                "created": datetime.now().isoformat(),
            }

            if mapped_meta.get("tags"):
                frontmatter["tags"] = mapped_meta["tags"]

            if mapped_meta.get("author"):
                frontmatter["author"] = mapped_meta["author"]

            # Add custom metadata
            for key, value in metadata.items():
                if key not in ["title", "content", "source_file"]:
                    frontmatter[key] = value

            # Convert frontmatter to YAML
            frontmatter_yaml = ""
            if HAS_YAML:
                frontmatter_yaml = "---\n" + yaml.dump(frontmatter, default_flow_style=False) + "---\n\n"
            else:
                # Simple frontmatter without YAML
                frontmatter_yaml = "---\n"
                for key, value in frontmatter.items():
                    frontmatter_yaml += f"{key}: {value}\n"
                frontmatter_yaml += "---\n\n"

            # Process markdown for Obsidian
            processed_markdown = self._process_obsidian_links(markdown_text)

            # Write file
            content = frontmatter_yaml + processed_markdown
            file_path.write_text(content, encoding="utf-8")

            return ExportResult(
                export_id=str(uuid.uuid4()),
                platform=ExportPlatform.OBSIDIAN,
                status=ExportStatus.COMPLETED,
                exported_id=filename,
                exported_url=None,  # Obsidian uses local files
                metadata={"filename": filename, "file_path": str(file_path)}
            )

        except Exception as e:
            logger.error(f"Obsidian export error: {e}")
            return ExportResult(
                export_id="",
                platform=ExportPlatform.OBSIDIAN,
                status=ExportStatus.FAILED,
                error=str(e)
            )

    def _title_to_filename(self, title: str) -> str:
        """Convert title to filename."""
        # Remove special characters, replace spaces with hyphens
        filename = re.sub(r'[^\w\s-]', '', title)
        filename = re.sub(r'[-\s]+', '-', filename)
        return filename.lower()

    def _process_obsidian_links(self, markdown_text: str) -> str:
        """Process markdown links for Obsidian format."""
        # Convert standard markdown links to Obsidian [[links]]
        # This is simplified - full implementation would handle more cases
        text = markdown_text
        
        # Convert [text](file.md) to [[file]]
        text = re.sub(
            r'\[([^\]]+)\]\(([^)]+\.md)\)',
            r'[[\2]]',
            text
        )
        
        return text

    def get_export_url(self, export_id: str) -> Optional[str]:
        """Get URL for exported content."""
        # Obsidian uses local files, no URL
        return None

