"""
Cloud storage management window for MarkItDown GUI.

Features:
- Unified cloud explorer
- Multiple provider support
- Drag & drop
- Sync status
- Credential management
- Offline mode
- Conflict resolution
"""

import customtkinter as ctk
from tkinter import messagebox
from pathlib import Path
from typing import Optional, Dict, Any
import logging

from gui.core.cloud_storage import CloudStorageManager, CloudProvider
from gui.integrations.google_drive import GoogleDriveProvider
from gui.integrations.dropbox_provider import DropboxProvider
from gui.integrations.onedrive_provider import OneDriveProvider
from gui.integrations.aws_s3_provider import AWSS3Provider
from gui.components.cloud_explorer import (
    CloudExplorerPanel,
    CloudCredentialsDialog,
    SyncStatusPanel,
)

logger = logging.getLogger(__name__)


class CloudStorageWindow(ctk.CTk):
    """Main window for cloud storage management."""

    def __init__(self, **kwargs) -> None:
        """
        Initialize cloud storage window.
        
        Args:
            **kwargs: Additional CTk arguments
        """
        super().__init__(**kwargs)
        self.cloud_manager = CloudStorageManager()
        self._register_providers()

        self._setup_window()
        self._create_layout()

        logger.info("Cloud storage window initialized")

    def _register_providers(self) -> None:
        """Register all cloud providers."""
        self.cloud_manager.register_provider(GoogleDriveProvider())
        self.cloud_manager.register_provider(DropboxProvider())
        self.cloud_manager.register_provider(OneDriveProvider())
        self.cloud_manager.register_provider(AWSS3Provider())

    def _setup_window(self) -> None:
        """Configure window properties."""
        self.title("MarkItDown - Cloud Storage")
        self.geometry("1400x900")
        self.minsize(1200, 700)

    def _create_layout(self) -> None:
        """Create main layout."""
        # Top toolbar
        toolbar = ctk.CTkFrame(self)
        toolbar.pack(fill="x", padx=10, pady=10)

        ctk.CTkLabel(
            toolbar,
            text="Cloud Storage",
            font=ctk.CTkFont(size=18, weight="bold"),
        ).pack(side="left", padx=10)

        # Provider buttons
        provider_frame = ctk.CTkFrame(toolbar)
        provider_frame.pack(side="right", padx=10)

        providers = [
            ("Google Drive", CloudProvider.GOOGLE_DRIVE),
            ("Dropbox", CloudProvider.DROPBOX),
            ("OneDrive", CloudProvider.ONEDRIVE),
            ("AWS S3", CloudProvider.AWS_S3),
        ]

        for name, provider in providers:
            btn = ctk.CTkButton(
                provider_frame,
                text=f"Connect {name}",
                command=lambda p=provider: self._connect_provider(p),
                width=120,
            )
            btn.pack(side="left", padx=2)

        # Main content
        main_frame = ctk.CTkFrame(self)
        main_frame.pack(fill="both", expand=True, padx=10, pady=10)

        # Left: Explorer
        left_frame = ctk.CTkFrame(main_frame)
        left_frame.pack(side="left", fill="both", expand=True, padx=5)

        self.explorer = CloudExplorerPanel(
            left_frame,
            self.cloud_manager,
            on_file_selected=self._on_file_selected,
        )
        self.explorer.pack(fill="both", expand=True)

        # Right: Sync status and settings
        right_frame = ctk.CTkFrame(main_frame)
        right_frame.pack(side="right", fill="y", padx=5)

        # Sync status
        self.sync_panel = SyncStatusPanel(
            right_frame,
            self.cloud_manager,
        )
        self.sync_panel.pack(fill="both", expand=True, padx=5, pady=5)

        # Credentials management
        creds_frame = ctk.CTkFrame(right_frame)
        creds_frame.pack(fill="x", padx=5, pady=5)

        ctk.CTkLabel(
            creds_frame,
            text="Credentials",
            font=ctk.CTkFont(size=12, weight="bold"),
        ).pack(pady=5)

        ctk.CTkButton(
            creds_frame,
            text="Manage Credentials",
            command=self._manage_credentials,
            width=150,
        ).pack(pady=5)

    def _connect_provider(self, provider: CloudProvider) -> None:
        """Connect to cloud provider."""
        provider_obj = self.cloud_manager.get_provider(provider)
        if not provider_obj:
            messagebox.showerror("Error", "Provider not available")
            return

        # Show credentials dialog
        dialog = CloudCredentialsDialog(
            self,
            provider,
            on_save=lambda creds: self._save_and_authenticate(provider, creds),
        )
        dialog.wait_window()

    def _save_and_authenticate(self, provider: CloudProvider, credentials: Dict[str, Any]) -> None:
        """Save credentials and authenticate."""
        if self.cloud_manager.authenticate_provider(provider, credentials):
            messagebox.showinfo("Success", f"{provider.value} connected successfully!")
            # Update explorer
            provider_name_map = {
                CloudProvider.GOOGLE_DRIVE: "Google Drive",
                CloudProvider.DROPBOX: "Dropbox",
                CloudProvider.ONEDRIVE: "OneDrive",
                CloudProvider.AWS_S3: "AWS S3",
            }
            self.explorer.provider_var.set(provider_name_map.get(provider, ""))
            self.explorer._change_provider(provider_name_map.get(provider, ""))
        else:
            messagebox.showerror("Error", f"Failed to connect to {provider.value}")

    def _on_file_selected(self, file: Any) -> None:
        """Handle file selection."""
        # Handle file selection for conversion
        pass

    def _manage_credentials(self) -> None:
        """Manage credentials for all providers."""
        messagebox.showinfo("Info", "Credential management - select provider to configure")

    def run(self) -> None:
        """Start the window."""
        logger.info("Starting cloud storage window")
        self.mainloop()


def show_cloud_storage() -> None:
    """Show cloud storage window."""
    window = CloudStorageWindow()
    window.run()

