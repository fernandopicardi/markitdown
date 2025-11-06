"""
Platform export window for MarkItDown GUI.

Features:
- Unified export interface
- Platform selection
- Field mapping
- Preview before export
- Export history
- Platform-specific templates
"""

import customtkinter as ctk
from tkinter import messagebox
from pathlib import Path
from typing import Optional, Dict, Any
import logging
import uuid

from gui.core.exporters import (
    ExportManager,
    ExportPlatform,
    ExportMapping,
)
from gui.exporters import (
    NotionExporter,
    ConfluenceExporter,
    WordPressExporter,
    MediumExporter,
    GitHubWikiExporter,
    ObsidianExporter,
)
from gui.components.export_ui import (
    PlatformSelector,
    FieldMappingPanel,
    ExportPreviewPanel,
    ExportHistoryPanel,
)

logger = logging.getLogger(__name__)


class PlatformExportWindow(ctk.CTk):
    """Main window for platform exports."""

    def __init__(
        self,
        markdown_text: str = "",
        metadata: Optional[Dict[str, Any]] = None,
        **kwargs
    ) -> None:
        """
        Initialize export window.
        
        Args:
            markdown_text: Markdown content to export
            metadata: Content metadata
            **kwargs: Additional CTk arguments
        """
        super().__init__(**kwargs)
        self.markdown_text = markdown_text
        self.metadata = metadata or {}
        self.export_manager = ExportManager()
        self.selected_platform: Optional[ExportPlatform] = None

        self._register_exporters()
        self._setup_window()
        self._create_layout()

        logger.info("Platform export window initialized")

    def _register_exporters(self) -> None:
        """Register all exporters."""
        self.export_manager.register_exporter(NotionExporter())
        self.export_manager.register_exporter(ConfluenceExporter())
        self.export_manager.register_exporter(WordPressExporter())
        self.export_manager.register_exporter(MediumExporter())
        self.export_manager.register_exporter(GitHubWikiExporter())
        self.export_manager.register_exporter(ObsidianExporter())

    def _setup_window(self) -> None:
        """Configure window properties."""
        self.title("MarkItDown - Platform Export")
        self.geometry("1400x900")
        self.minsize(1200, 700)

    def _create_layout(self) -> None:
        """Create main layout."""
        # Top toolbar
        toolbar = ctk.CTkFrame(self)
        toolbar.pack(fill="x", padx=10, pady=10)

        ctk.CTkLabel(
            toolbar,
            text="Platform Export",
            font=ctk.CTkFont(size=18, weight="bold"),
        ).pack(side="left", padx=10)

        # Main content
        main_frame = ctk.CTkFrame(self)
        main_frame.pack(fill="both", expand=True, padx=10, pady=10)

        # Left: Platform selection and mapping
        left_frame = ctk.CTkFrame(main_frame)
        left_frame.pack(side="left", fill="both", expand=False, padx=5)

        # Platform selector
        self.platform_selector = PlatformSelector(
            left_frame,
            on_platform_selected=self._on_platform_selected,
        )
        self.platform_selector.pack(fill="x", padx=5, pady=5)

        # Field mapping
        self.mapping_panel = FieldMappingPanel(left_frame)
        self.mapping_panel.pack(fill="x", padx=5, pady=5)

        # Center: Preview
        center_frame = ctk.CTkFrame(main_frame)
        center_frame.pack(side="left", fill="both", expand=True, padx=5)

        self.preview_panel = ExportPreviewPanel(center_frame)
        self.preview_panel.pack(fill="both", expand=True, padx=5, pady=5)

        # Update preview
        if self.markdown_text:
            self.preview_panel.set_preview(self.markdown_text, self.metadata)

        # Right: History and actions
        right_frame = ctk.CTkFrame(main_frame)
        right_frame.pack(side="right", fill="y", padx=5)

        # Export button
        export_frame = ctk.CTkFrame(right_frame)
        export_frame.pack(fill="x", padx=5, pady=5)

        ctk.CTkButton(
            export_frame,
            text="Export",
            command=self._export,
            width=150,
            font=ctk.CTkFont(size=14, weight="bold"),
        ).pack(pady=10)

        ctk.CTkButton(
            export_frame,
            text="Configure Platform",
            command=self._configure_platform,
            width=150,
        ).pack(pady=5)

        # History
        self.history_panel = ExportHistoryPanel(
            right_frame,
            self.export_manager,
        )
        self.history_panel.pack(fill="both", expand=True, padx=5, pady=5)

    def _on_platform_selected(self, platform: ExportPlatform) -> None:
        """Handle platform selection."""
        self.selected_platform = platform
        exporter = self.export_manager.get_exporter(platform)
        if exporter and exporter.authenticated:
            messagebox.showinfo("Platform Selected", f"{platform.value} is ready for export")
        else:
            messagebox.showwarning(
                "Authentication Required",
                f"Please configure {platform.value} credentials first"
            )

    def _configure_platform(self) -> None:
        """Configure selected platform."""
        if not self.selected_platform:
            messagebox.showwarning("No Platform", "Please select a platform first")
            return

        exporter = self.export_manager.get_exporter(self.selected_platform)
        if not exporter:
            return

        # Show credentials dialog
        dialog = self._create_credentials_dialog(self.selected_platform)
        dialog.wait_window()

    def _create_credentials_dialog(self, platform: ExportPlatform) -> ctk.CTkToplevel:
        """Create credentials dialog for platform."""
        dialog = ctk.CTkToplevel(self)
        dialog.title(f"Configure {platform.value}")
        dialog.geometry("500x400")

        credentials = {}

        if platform == ExportPlatform.NOTION:
            ctk.CTkLabel(dialog, text="Notion Integration Token:").pack(pady=10)
            token_var = ctk.StringVar()
            ctk.CTkEntry(
                dialog,
                textvariable=token_var,
                width=400,
                show="*",
            ).pack(pady=5)
            credentials["notion_token"] = token_var

        elif platform == ExportPlatform.CONFLUENCE:
            ctk.CTkLabel(dialog, text="Base URL:").pack(pady=5)
            url_var = ctk.StringVar()
            ctk.CTkEntry(dialog, textvariable=url_var, width=400).pack(pady=5)

            ctk.CTkLabel(dialog, text="Username:").pack(pady=5)
            user_var = ctk.StringVar()
            ctk.CTkEntry(dialog, textvariable=user_var, width=400).pack(pady=5)

            ctk.CTkLabel(dialog, text="API Token:").pack(pady=5)
            token_var = ctk.StringVar()
            ctk.CTkEntry(dialog, textvariable=token_var, width=400, show="*").pack(pady=5)
            credentials = {"base_url": url_var, "username": user_var, "api_token": token_var}

        elif platform == ExportPlatform.WORDPRESS:
            ctk.CTkLabel(dialog, text="WordPress URL:").pack(pady=5)
            url_var = ctk.StringVar()
            ctk.CTkEntry(dialog, textvariable=url_var, width=400).pack(pady=5)

            ctk.CTkLabel(dialog, text="Username:").pack(pady=5)
            user_var = ctk.StringVar()
            ctk.CTkEntry(dialog, textvariable=user_var, width=400).pack(pady=5)

            ctk.CTkLabel(dialog, text="Application Password:").pack(pady=5)
            pass_var = ctk.StringVar()
            ctk.CTkEntry(dialog, textvariable=pass_var, width=400, show="*").pack(pady=5)
            credentials = {"base_url": url_var, "username": user_var, "application_password": pass_var}

        elif platform == ExportPlatform.MEDIUM:
            ctk.CTkLabel(dialog, text="Medium Access Token:").pack(pady=10)
            token_var = ctk.StringVar()
            ctk.CTkEntry(
                dialog,
                textvariable=token_var,
                width=400,
                show="*",
            ).pack(pady=5)
            credentials["access_token"] = token_var

        elif platform == ExportPlatform.GITHUB_WIKI:
            ctk.CTkLabel(dialog, text="Wiki Path:").pack(pady=5)
            path_var = ctk.StringVar()
            ctk.CTkEntry(dialog, textvariable=path_var, width=400).pack(pady=5)

            ctk.CTkLabel(dialog, text="Wiki URL (to clone):").pack(pady=5)
            url_var = ctk.StringVar()
            ctk.CTkEntry(dialog, textvariable=url_var, width=400).pack(pady=5)
            credentials = {"wiki_path": path_var, "wiki_url": url_var}

        elif platform == ExportPlatform.OBSIDIAN:
            ctk.CTkLabel(dialog, text="Vault Path:").pack(pady=10)
            path_var = ctk.StringVar()
            ctk.CTkEntry(dialog, textvariable=path_var, width=400).pack(pady=5)
            credentials["vault_path"] = path_var

        # Buttons
        button_frame = ctk.CTkFrame(dialog)
        button_frame.pack(fill="x", padx=20, pady=10)

        def save_credentials():
            # Extract values from StringVars
            creds = {}
            for key, value in credentials.items():
                if isinstance(value, ctk.StringVar):
                    creds[key] = value.get()
                else:
                    creds[key] = value

            if self.export_manager.authenticate_exporter(platform, creds):
                messagebox.showinfo("Success", f"{platform.value} configured successfully!")
                dialog.destroy()
            else:
                messagebox.showerror("Error", f"Failed to authenticate with {platform.value}")

        ctk.CTkButton(
            button_frame,
            text="Save",
            command=save_credentials,
            width=100,
        ).pack(side="right", padx=5)

        ctk.CTkButton(
            button_frame,
            text="Cancel",
            command=dialog.destroy,
            width=100,
        ).pack(side="right", padx=5)

        return dialog

    def _export(self) -> None:
        """Export to selected platform."""
        if not self.selected_platform:
            messagebox.showwarning("No Platform", "Please select a platform first")
            return

        if not self.markdown_text:
            messagebox.showwarning("No Content", "No content to export")
            return

        exporter = self.export_manager.get_exporter(self.selected_platform)
        if not exporter or not exporter.authenticated:
            messagebox.showwarning(
                "Not Authenticated",
                f"Please configure {self.selected_platform.value} first"
            )
            return

        # Get mapping
        mapping = self.mapping_panel.get_mapping()
        exporter.set_mapping(mapping)

        # Get destination (if needed)
        destination = None
        if self.selected_platform == ExportPlatform.NOTION:
            destination = self.metadata.get("database_id")
        elif self.selected_platform == ExportPlatform.CONFLUENCE:
            destination = self.metadata.get("space_key")

        # Export
        try:
            result = self.export_manager.export_to_platform(
                self.selected_platform,
                self.markdown_text,
                {**self.metadata, "source_file": self.metadata.get("source_file", "unknown")},
                destination
            )

            if result.status.value == "completed":
                messagebox.showinfo(
                    "Export Successful",
                    f"Exported to {self.selected_platform.value}!\n\n"
                    f"URL: {result.exported_url or 'N/A'}"
                )
                self.history_panel._refresh_history()
            else:
                messagebox.showerror(
                    "Export Failed",
                    f"Failed to export: {result.error}"
                )

        except Exception as e:
            logger.error(f"Export error: {e}")
            messagebox.showerror("Error", f"Export failed: {e}")

    def set_content(self, markdown_text: str, metadata: Optional[Dict[str, Any]] = None) -> None:
        """
        Set content to export.
        
        Args:
            markdown_text: Markdown content
            metadata: Content metadata
        """
        self.markdown_text = markdown_text
        self.metadata = metadata or {}
        if hasattr(self, 'preview_panel'):
            self.preview_panel.set_preview(markdown_text, self.metadata)

    def run(self) -> None:
        """Start the window."""
        logger.info("Starting platform export window")
        self.mainloop()


def show_export_window(markdown_text: str = "", metadata: Optional[Dict[str, Any]] = None) -> None:
    """
    Show platform export window.
    
    Args:
        markdown_text: Markdown content to export
        metadata: Content metadata
    """
    window = PlatformExportWindow(markdown_text=markdown_text, metadata=metadata)
    window.run()

