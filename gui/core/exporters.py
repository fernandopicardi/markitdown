"""
Platform exporters system for MarkItDown GUI.

This module provides exporters for popular platforms:
Notion, Confluence, WordPress, Medium, GitHub Wiki, Obsidian.
"""

import logging
from pathlib import Path
from typing import Dict, List, Optional, Any, Callable
from abc import ABC, abstractmethod
from dataclasses import dataclass, field
from enum import Enum
from datetime import datetime
import json

logger = logging.getLogger(__name__)


class ExportPlatform(Enum):
    """Export platforms."""

    NOTION = "notion"
    CONFLUENCE = "confluence"
    WORDPRESS = "wordpress"
    MEDIUM = "medium"
    GITHUB_WIKI = "github_wiki"
    OBSIDIAN = "obsidian"


class ExportStatus(Enum):
    """Export status."""

    PENDING = "pending"
    EXPORTING = "exporting"
    COMPLETED = "completed"
    FAILED = "failed"
    CANCELLED = "cancelled"


@dataclass
class ExportMapping:
    """Field mapping for export."""

    title_field: str = "title"
    content_field: str = "content"
    author_field: Optional[str] = None
    date_field: Optional[str] = None
    tags_field: Optional[str] = None
    categories_field: Optional[str] = None
    custom_fields: Dict[str, str] = field(default_factory=dict)


@dataclass
class ExportResult:
    """Result of export operation."""

    export_id: str
    platform: ExportPlatform
    status: ExportStatus
    exported_url: Optional[str] = None
    exported_id: Optional[str] = None
    error: Optional[str] = None
    exported_at: datetime = field(default_factory=datetime.now)
    metadata: Dict[str, Any] = field(default_factory=dict)


@dataclass
class ExportHistory:
    """Export history entry."""

    export_id: str
    platform: ExportPlatform
    source_file: str
    destination: str
    status: ExportStatus
    exported_at: datetime
    metadata: Dict[str, Any] = field(default_factory=dict)


class AbstractExporter(ABC):
    """Abstract base class for platform exporters."""

    def __init__(self, platform: ExportPlatform) -> None:
        """
        Initialize exporter.
        
        Args:
            platform: Export platform
        """
        self.platform = platform
        self.authenticated = False
        self.credentials: Dict[str, Any] = {}
        self.mapping: ExportMapping = ExportMapping()

    @abstractmethod
    def authenticate(self, credentials: Dict[str, Any]) -> bool:
        """
        Authenticate with platform.
        
        Args:
            credentials: Authentication credentials
            
        Returns:
            True if authenticated successfully
        """
        pass

    @abstractmethod
    def export(
        self,
        markdown_text: str,
        metadata: Dict[str, Any],
        destination: Optional[str] = None
    ) -> ExportResult:
        """
        Export markdown to platform.
        
        Args:
            markdown_text: Markdown content
            metadata: Content metadata
            destination: Destination identifier (page ID, etc.)
            
        Returns:
            Export result
        """
        pass

    @abstractmethod
    def get_export_url(self, export_id: str) -> Optional[str]:
        """
        Get URL for exported content.
        
        Args:
            export_id: Export ID from platform
            
        Returns:
            URL or None
        """
        pass

    def set_mapping(self, mapping: ExportMapping) -> None:
        """
        Set field mapping.
        
        Args:
            mapping: Export mapping
        """
        self.mapping = mapping

    def _extract_metadata(self, metadata: Dict[str, Any]) -> Dict[str, Any]:
        """
        Extract metadata using mapping.
        
        Args:
            metadata: Source metadata
            
        Returns:
            Mapped metadata
        """
        mapped = {}
        if self.mapping.title_field:
            mapped["title"] = metadata.get(self.mapping.title_field, "")
        if self.mapping.author_field:
            mapped["author"] = metadata.get(self.mapping.author_field, "")
        if self.mapping.date_field:
            mapped["date"] = metadata.get(self.mapping.date_field, "")
        if self.mapping.tags_field:
            tags = metadata.get(self.mapping.tags_field, [])
            mapped["tags"] = tags if isinstance(tags, list) else [tags]
        if self.mapping.categories_field:
            categories = metadata.get(self.mapping.categories_field, [])
            mapped["categories"] = categories if isinstance(categories, list) else [categories]

        # Custom fields
        for target, source in self.mapping.custom_fields.items():
            mapped[target] = metadata.get(source, "")

        return mapped


class ExportManager:
    """Manages platform exporters."""

    def __init__(self, history_file: Optional[Path] = None) -> None:
        """
        Initialize export manager.
        
        Args:
            history_file: Path to export history file
        """
        if history_file is None:
            import os
            if os.name == "nt":  # Windows
                history_file = Path.home() / "AppData" / "Local" / "MarkItDown" / "export_history.json"
            else:  # Linux/Mac
                history_file = Path.home() / ".config" / "markitdown" / "export_history.json"
            history_file.parent.mkdir(parents=True, exist_ok=True)

        self.history_file = history_file
        self.exporters: Dict[ExportPlatform, AbstractExporter] = {}
        self.export_history: List[ExportHistory] = []
        self._load_history()

    def register_exporter(self, exporter: AbstractExporter) -> None:
        """
        Register an exporter.
        
        Args:
            exporter: Exporter instance
        """
        self.exporters[exporter.platform] = exporter
        logger.info(f"Registered exporter: {exporter.platform.value}")

    def get_exporter(self, platform: ExportPlatform) -> Optional[AbstractExporter]:
        """
        Get exporter by platform.
        
        Args:
            platform: Export platform
            
        Returns:
            Exporter or None
        """
        return self.exporters.get(platform)

    def authenticate_exporter(self, platform: ExportPlatform, credentials: Dict[str, Any]) -> bool:
        """
        Authenticate exporter.
        
        Args:
            platform: Export platform
            credentials: Authentication credentials
            
        Returns:
            True if authenticated successfully
        """
        exporter = self.get_exporter(platform)
        if not exporter:
            return False

        return exporter.authenticate(credentials)

    def export_to_platform(
        self,
        platform: ExportPlatform,
        markdown_text: str,
        metadata: Dict[str, Any],
        destination: Optional[str] = None
    ) -> ExportResult:
        """
        Export to platform.
        
        Args:
            platform: Export platform
            markdown_text: Markdown content
            metadata: Content metadata
            destination: Destination identifier
            
        Returns:
            Export result
        """
        exporter = self.get_exporter(platform)
        if not exporter:
            return ExportResult(
                export_id="",
                platform=platform,
                status=ExportStatus.FAILED,
                error="Exporter not found"
            )

        if not exporter.authenticated:
            return ExportResult(
                export_id="",
                platform=platform,
                status=ExportStatus.FAILED,
                error="Exporter not authenticated"
            )

        try:
            result = exporter.export(markdown_text, metadata, destination)
            self._save_history(result, metadata)
            return result
        except Exception as e:
            logger.error(f"Export error: {e}")
            return ExportResult(
                export_id="",
                platform=platform,
                status=ExportStatus.FAILED,
                error=str(e)
            )

    def _save_history(self, result: ExportResult, metadata: Dict[str, Any]) -> None:
        """Save export to history."""
        history_entry = ExportHistory(
            export_id=result.export_id,
            platform=result.platform,
            source_file=metadata.get("source_file", ""),
            destination=result.exported_url or result.exported_id or "",
            status=result.status,
            exported_at=result.exported_at,
            metadata=result.metadata,
        )
        self.export_history.append(history_entry)
        self._persist_history()

    def _load_history(self) -> None:
        """Load export history."""
        if self.history_file.exists():
            try:
                with open(self.history_file, "r", encoding="utf-8") as f:
                    data = json.load(f)
                # Reconstruct history (simplified)
                self.export_history = []
            except Exception as e:
                logger.error(f"Failed to load export history: {e}")

    def _persist_history(self) -> None:
        """Persist export history."""
        try:
            data = [
                {
                    "export_id": h.export_id,
                    "platform": h.platform.value,
                    "source_file": h.source_file,
                    "destination": h.destination,
                    "status": h.status.value,
                    "exported_at": h.exported_at.isoformat(),
                    "metadata": h.metadata,
                }
                for h in self.export_history[-100:]  # Keep last 100
            ]
            with open(self.history_file, "w", encoding="utf-8") as f:
                json.dump(data, f, indent=2, ensure_ascii=False)
        except Exception as e:
            logger.error(f"Failed to save export history: {e}")

    def get_history(self, platform: Optional[ExportPlatform] = None) -> List[ExportHistory]:
        """
        Get export history.
        
        Args:
            platform: Filter by platform (None for all)
            
        Returns:
            List of export history entries
        """
        if platform:
            return [h for h in self.export_history if h.platform == platform]
        return self.export_history.copy()

