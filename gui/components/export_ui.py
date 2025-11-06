"""
Export UI components for MarkItDown GUI.
"""

import customtkinter as ctk
from tkinter import messagebox
from pathlib import Path
from typing import Optional, Callable, Dict, Any
import logging

from gui.core.exporters import (
    ExportManager,
    ExportPlatform,
    ExportMapping,
    ExportHistory,
)

logger = logging.getLogger(__name__)


class PlatformSelector(ctk.CTkFrame):
    """Platform selection component."""

    def __init__(
        self,
        master: Any,
        on_platform_selected: Optional[Callable[[ExportPlatform], None]] = None,
        **kwargs
    ) -> None:
        """
        Initialize platform selector.
        
        Args:
            master: Parent widget
            on_platform_selected: Callback when platform is selected
            **kwargs: Additional CTkFrame arguments
        """
        super().__init__(master, **kwargs)
        self.on_platform_selected = on_platform_selected
        self.selected_platform: Optional[ExportPlatform] = None
        self._create_widgets()

    def _create_widgets(self) -> None:
        """Create selector widgets."""
        ctk.CTkLabel(
            self,
            text="Select Export Platform",
            font=ctk.CTkFont(size=14, weight="bold"),
        ).pack(pady=10)

        platforms = [
            ("Notion", ExportPlatform.NOTION),
            ("Confluence", ExportPlatform.CONFLUENCE),
            ("WordPress", ExportPlatform.WORDPRESS),
            ("Medium", ExportPlatform.MEDIUM),
            ("GitHub Wiki", ExportPlatform.GITHUB_WIKI),
            ("Obsidian", ExportPlatform.OBSIDIAN),
        ]

        for name, platform in platforms:
            btn = ctk.CTkButton(
                self,
                text=name,
                command=lambda p=platform: self._select_platform(p),
                width=200,
            )
            btn.pack(pady=5)

    def _select_platform(self, platform: ExportPlatform) -> None:
        """Select platform."""
        self.selected_platform = platform
        if self.on_platform_selected:
            self.on_platform_selected(platform)


class FieldMappingPanel(ctk.CTkFrame):
    """Field mapping configuration panel."""

    def __init__(
        self,
        master: Any,
        **kwargs
    ) -> None:
        """
        Initialize field mapping panel.
        
        Args:
            master: Parent widget
            **kwargs: Additional CTkFrame arguments
        """
        super().__init__(master, **kwargs)
        self.mapping = ExportMapping()
        self._create_widgets()

    def _create_widgets(self) -> None:
        """Create mapping widgets."""
        ctk.CTkLabel(
            self,
            text="Field Mapping",
            font=ctk.CTkFont(size=12, weight="bold"),
        ).pack(pady=5)

        # Title
        title_frame = ctk.CTkFrame(self)
        title_frame.pack(fill="x", padx=10, pady=5)

        ctk.CTkLabel(title_frame, text="Title:").pack(side="left", padx=5)
        self.title_var = ctk.StringVar(value="title")
        ctk.CTkEntry(title_frame, textvariable=self.title_var, width=150).pack(side="left", padx=5)

        # Author
        author_frame = ctk.CTkFrame(self)
        author_frame.pack(fill="x", padx=10, pady=5)

        ctk.CTkLabel(author_frame, text="Author:").pack(side="left", padx=5)
        self.author_var = ctk.StringVar(value="author")
        ctk.CTkEntry(author_frame, textvariable=self.author_var, width=150).pack(side="left", padx=5)

        # Tags
        tags_frame = ctk.CTkFrame(self)
        tags_frame.pack(fill="x", padx=10, pady=5)

        ctk.CTkLabel(tags_frame, text="Tags:").pack(side="left", padx=5)
        self.tags_var = ctk.StringVar(value="tags")
        ctk.CTkEntry(tags_frame, textvariable=self.tags_var, width=150).pack(side="left", padx=5)

    def get_mapping(self) -> ExportMapping:
        """Get current mapping."""
        self.mapping.title_field = self.title_var.get()
        self.mapping.author_field = self.author_var.get() if self.author_var.get() else None
        self.mapping.tags_field = self.tags_var.get() if self.tags_var.get() else None
        return self.mapping


class ExportPreviewPanel(ctk.CTkFrame):
    """Preview panel before export."""

    def __init__(
        self,
        master: Any,
        **kwargs
    ) -> None:
        """
        Initialize preview panel.
        
        Args:
            master: Parent widget
            **kwargs: Additional CTkFrame arguments
        """
        super().__init__(master, **kwargs)
        self._create_widgets()

    def _create_widgets(self) -> None:
        """Create preview widgets."""
        ctk.CTkLabel(
            self,
            text="Export Preview",
            font=ctk.CTkFont(size=12, weight="bold"),
        ).pack(pady=5)

        self.preview_text = ctk.CTkTextbox(self, height=300)
        self.preview_text.pack(fill="both", expand=True, padx=10, pady=10)

    def set_preview(self, content: str, metadata: Dict[str, Any]) -> None:
        """
        Set preview content.
        
        Args:
            content: Markdown content
            metadata: Metadata
        """
        self.preview_text.delete("1.0", "end")
        preview = f"Title: {metadata.get('title', 'Untitled')}\n"
        preview += f"Author: {metadata.get('author', 'Unknown')}\n"
        preview += f"Tags: {', '.join(metadata.get('tags', []))}\n"
        preview += f"\n---\n\n{content[:500]}..."
        self.preview_text.insert("1.0", preview)


class ExportHistoryPanel(ctk.CTkFrame):
    """Export history panel."""

    def __init__(
        self,
        master: Any,
        export_manager: ExportManager,
        **kwargs
    ) -> None:
        """
        Initialize history panel.
        
        Args:
            master: Parent widget
            export_manager: ExportManager instance
            **kwargs: Additional CTkFrame arguments
        """
        super().__init__(master, **kwargs)
        self.export_manager = export_manager
        self._create_widgets()
        self._refresh_history()

    def _create_widgets(self) -> None:
        """Create history widgets."""
        ctk.CTkLabel(
            self,
            text="Export History",
            font=ctk.CTkFont(size=12, weight="bold"),
        ).pack(pady=5)

        # Filter
        filter_frame = ctk.CTkFrame(self)
        filter_frame.pack(fill="x", padx=10, pady=5)

        ctk.CTkLabel(filter_frame, text="Platform:").pack(side="left", padx=5)
        self.filter_var = ctk.StringVar(value="all")
        filter_menu = ctk.CTkOptionMenu(
            filter_frame,
            values=["all", "notion", "confluence", "wordpress", "medium", "github_wiki", "obsidian"],
            variable=self.filter_var,
            command=self._filter_history,
            width=150,
        )
        filter_menu.pack(side="left", padx=5)

        # History list
        self.history_listbox = ctk.CTkTextbox(self, height=300)
        self.history_listbox.pack(fill="both", expand=True, padx=10, pady=10)

        # Refresh button
        ctk.CTkButton(
            self,
            text="Refresh",
            command=self._refresh_history,
            width=100,
        ).pack(pady=5)

    def _refresh_history(self) -> None:
        """Refresh history display."""
        self.history_listbox.delete("1.0", "end")

        filter_platform = self.filter_var.get()
        if filter_platform == "all":
            history = self.export_manager.get_history()
        else:
            platform = ExportPlatform(filter_platform)
            history = self.export_manager.get_history(platform)

        if not history:
            self.history_listbox.insert("1.0", "No export history")
            return

        for entry in history[-20:]:  # Last 20
            status_icon = "✓" if entry.status.value == "completed" else "✗"
            self.history_listbox.insert(
                "end",
                f"{status_icon} {entry.platform.value}: {entry.source_file}\n"
                f"   Destination: {entry.destination}\n"
                f"   Date: {entry.exported_at.strftime('%Y-%m-%d %H:%M')}\n\n"
            )

    def _filter_history(self, platform: str) -> None:
        """Filter history by platform."""
        self._refresh_history()

