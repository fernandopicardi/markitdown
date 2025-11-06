"""
Cloud storage explorer component for MarkItDown GUI.
"""

import customtkinter as ctk
from tkinter import messagebox
from pathlib import Path
from typing import Optional, Callable, List
import logging

from gui.core.cloud_storage import (
    CloudStorageManager,
    CloudProvider,
    CloudFile,
    SyncStatus,
)

logger = logging.getLogger(__name__)


class CloudExplorerPanel(ctk.CTkFrame):
    """Cloud file explorer panel."""

    def __init__(
        self,
        master: Any,
        cloud_manager: CloudStorageManager,
        on_file_selected: Optional[Callable[[CloudFile], None]] = None,
        **kwargs
    ) -> None:
        """
        Initialize cloud explorer.
        
        Args:
            master: Parent widget
            cloud_manager: CloudStorageManager instance
            on_file_selected: Callback when file is selected
            **kwargs: Additional CTkFrame arguments
        """
        super().__init__(master, **kwargs)
        self.cloud_manager = cloud_manager
        self.on_file_selected = on_file_selected
        self.current_provider: Optional[CloudProvider] = None
        self.current_folder_id: Optional[str] = None
        self.current_files: List[CloudFile] = []

        self._create_widgets()

    def _create_widgets(self) -> None:
        """Create explorer widgets."""
        # Toolbar
        toolbar = ctk.CTkFrame(self)
        toolbar.pack(fill="x", padx=5, pady=5)

        # Provider selection
        provider_frame = ctk.CTkFrame(toolbar)
        provider_frame.pack(side="left", padx=5)

        ctk.CTkLabel(provider_frame, text="Provider:").pack(side="left", padx=5)
        self.provider_var = ctk.StringVar(value="")
        provider_menu = ctk.CTkOptionMenu(
            provider_frame,
            values=["", "Google Drive", "Dropbox", "OneDrive", "AWS S3"],
            variable=self.provider_var,
            command=self._change_provider,
            width=150,
        )
        provider_menu.pack(side="left", padx=5)

        # Navigation
        nav_frame = ctk.CTkFrame(toolbar)
        nav_frame.pack(side="right", padx=5)

        ctk.CTkButton(
            nav_frame,
            text="◀ Back",
            command=self._go_back,
            width=80,
        ).pack(side="left", padx=2)

        ctk.CTkButton(
            nav_frame,
            text="Refresh",
            command=self._refresh,
            width=80,
        ).pack(side="left", padx=2)

        # File list
        list_frame = ctk.CTkFrame(self)
        list_frame.pack(fill="both", expand=True, padx=5, pady=5)

        ctk.CTkLabel(
            list_frame,
            text="Cloud Files",
            font=ctk.CTkFont(size=12, weight="bold"),
        ).pack(pady=5)

        self.file_listbox = ctk.CTkTextbox(list_frame)
        self.file_listbox.pack(fill="both", expand=True)

        # Actions
        action_frame = ctk.CTkFrame(self)
        action_frame.pack(fill="x", padx=5, pady=5)

        ctk.CTkButton(
            action_frame,
            text="Download",
            command=self._download_selected,
            width=100,
        ).pack(side="left", padx=5)

        ctk.CTkButton(
            action_frame,
            text="Upload",
            command=self._upload_file,
            width=100,
        ).pack(side="left", padx=5)

        ctk.CTkButton(
            action_frame,
            text="Share Link",
            command=self._get_share_link,
            width=100,
        ).pack(side="left", padx=5)

    def _change_provider(self, provider_name: str) -> None:
        """Change cloud provider."""
        provider_map = {
            "Google Drive": CloudProvider.GOOGLE_DRIVE,
            "Dropbox": CloudProvider.DROPBOX,
            "OneDrive": CloudProvider.ONEDRIVE,
            "AWS S3": CloudProvider.AWS_S3,
        }
        self.current_provider = provider_map.get(provider_name)
        self.current_folder_id = None
        self._refresh()

    def _refresh(self) -> None:
        """Refresh file list."""
        if not self.current_provider:
            self.file_listbox.delete("1.0", "end")
            self.file_listbox.insert("1.0", "Select a cloud provider")
            return

        provider = self.cloud_manager.get_provider(self.current_provider)
        if not provider or not provider.authenticated:
            self.file_listbox.delete("1.0", "end")
            self.file_listbox.insert("1.0", "Provider not authenticated")
            return

        self.current_files = self.cloud_manager.list_files(
            self.current_provider,
            self.current_folder_id
        )

        self.file_listbox.delete("1.0", "end")
        for file in self.current_files:
            icon = "📁" if file.is_folder else "📄"
            self.file_listbox.insert(
                "end",
                f"{icon} {file.name}\n"
                f"   Size: {file.size:,} bytes\n"
                f"   Modified: {file.modified_time.strftime('%Y-%m-%d %H:%M')}\n\n"
            )

    def _go_back(self) -> None:
        """Go back to parent folder."""
        if self.current_folder_id:
            # Navigate to parent (simplified)
            self.current_folder_id = None
            self._refresh()

    def _download_selected(self) -> None:
        """Download selected file."""
        if not self.current_files:
            messagebox.showwarning("No Selection", "Please select a file")
            return

        # Simplified: download first file
        file = self.current_files[0]
        if file.is_folder:
            messagebox.showinfo("Info", "Please select a file, not a folder")
            return

        from tkinter import filedialog
        save_path = filedialog.asksaveasfilename(
            title="Save File",
            initialfile=file.name,
        )
        if save_path:
            if self.cloud_manager.download_file(
                self.current_provider,
                file.file_id,
                Path(save_path)
            ):
                messagebox.showinfo("Success", "File downloaded!")
            else:
                messagebox.showerror("Error", "Failed to download file")

    def _upload_file(self) -> None:
        """Upload file to cloud."""
        from tkinter import filedialog
        file_path = filedialog.askopenfilename(title="Select File to Upload")
        if file_path and self.current_provider:
            file_id = self.cloud_manager.upload_file(
                self.current_provider,
                Path(file_path),
                Path(file_path).name,
                self.current_folder_id
            )
            if file_id:
                messagebox.showinfo("Success", "File uploaded!")
                self._refresh()
            else:
                messagebox.showerror("Error", "Failed to upload file")

    def _get_share_link(self) -> None:
        """Get shareable link for selected file."""
        if not self.current_files:
            messagebox.showwarning("No Selection", "Please select a file")
            return

        file = self.current_files[0]
        provider = self.cloud_manager.get_provider(self.current_provider)
        if provider:
            link = provider.get_share_link(file.file_id)
            if link:
                self.clipboard_clear()
                self.clipboard_append(link)
                messagebox.showinfo("Share Link", f"Link copied to clipboard:\n{link}")
            else:
                messagebox.showerror("Error", "Failed to get share link")


class CloudCredentialsDialog(ctk.CTkToplevel):
    """Dialog for cloud service credentials."""

    def __init__(
        self,
        parent: Any,
        provider: CloudProvider,
        on_save: Optional[Callable[[Dict[str, Any]], None]] = None,
        **kwargs
    ) -> None:
        """
        Initialize credentials dialog.
        
        Args:
            parent: Parent window
            provider: Cloud provider
            on_save: Callback when credentials are saved
            **kwargs: Additional CTkToplevel arguments
        """
        super().__init__(parent, **kwargs)
        self.provider = provider
        self.on_save = on_save
        self.credentials: Dict[str, Any] = {}

        self.title(f"Configure {provider.value}")
        self.geometry("500x400")

        self._create_widgets()

    def _create_widgets(self) -> None:
        """Create dialog widgets."""
        # Instructions
        instructions = ctk.CTkLabel(
            self,
            text=f"Enter credentials for {self.provider.value}",
            font=ctk.CTkFont(size=12),
        )
        instructions.pack(pady=10)

        # Credentials form
        form_frame = ctk.CTkFrame(self)
        form_frame.pack(fill="both", expand=True, padx=20, pady=10)

        if self.provider == CloudProvider.GOOGLE_DRIVE:
            ctk.CTkLabel(form_frame, text="Client Config (JSON):").pack(pady=5)
            self.config_text = ctk.CTkTextbox(form_frame, height=200)
            self.config_text.pack(fill="x", padx=10, pady=5)

        elif self.provider == CloudProvider.DROPBOX:
            ctk.CTkLabel(form_frame, text="Access Token:").pack(pady=5)
            self.token_var = ctk.StringVar()
            ctk.CTkEntry(
                form_frame,
                textvariable=self.token_var,
                width=400,
                show="*",
            ).pack(padx=10, pady=5)

        elif self.provider == CloudProvider.ONEDRIVE:
            ctk.CTkLabel(form_frame, text="Client ID:").pack(pady=5)
            self.client_id_var = ctk.StringVar()
            ctk.CTkEntry(
                form_frame,
                textvariable=self.client_id_var,
                width=400,
            ).pack(padx=10, pady=5)

        elif self.provider == CloudProvider.AWS_S3:
            ctk.CTkLabel(form_frame, text="Access Key ID:").pack(pady=5)
            self.access_key_var = ctk.StringVar()
            ctk.CTkEntry(
                form_frame,
                textvariable=self.access_key_var,
                width=400,
            ).pack(padx=10, pady=5)

            ctk.CTkLabel(form_frame, text="Secret Access Key:").pack(pady=5)
            self.secret_key_var = ctk.StringVar()
            ctk.CTkEntry(
                form_frame,
                textvariable=self.secret_key_var,
                width=400,
                show="*",
            ).pack(padx=10, pady=5)

            ctk.CTkLabel(form_frame, text="Region:").pack(pady=5)
            self.region_var = ctk.StringVar(value="us-east-1")
            ctk.CTkEntry(
                form_frame,
                textvariable=self.region_var,
                width=400,
            ).pack(padx=10, pady=5)

        # Buttons
        button_frame = ctk.CTkFrame(self)
        button_frame.pack(fill="x", padx=20, pady=10)

        ctk.CTkButton(
            button_frame,
            text="Cancel",
            command=self.destroy,
            width=100,
        ).pack(side="right", padx=5)

        ctk.CTkButton(
            button_frame,
            text="Save",
            command=self._save_credentials,
            width=100,
        ).pack(side="right", padx=5)

    def _save_credentials(self) -> None:
        """Save credentials."""
        if self.provider == CloudProvider.GOOGLE_DRIVE:
            import json
            try:
                config_text = self.config_text.get("1.0", "end-1c")
                self.credentials = {"client_config": json.loads(config_text)}
            except Exception as e:
                messagebox.showerror("Error", f"Invalid JSON: {e}")
                return

        elif self.provider == CloudProvider.DROPBOX:
            self.credentials = {"access_token": self.token_var.get()}

        elif self.provider == CloudProvider.ONEDRIVE:
            self.credentials = {"client_id": self.client_id_var.get()}

        elif self.provider == CloudProvider.AWS_S3:
            self.credentials = {
                "access_key_id": self.access_key_var.get(),
                "secret_access_key": self.secret_key_var.get(),
                "region": self.region_var.get(),
            }

        if self.on_save:
            self.on_save(self.credentials)
        self.destroy()


class SyncStatusPanel(ctk.CTkFrame):
    """Panel for sync status and queue."""

    def __init__(
        self,
        master: Any,
        cloud_manager: CloudStorageManager,
        **kwargs
    ) -> None:
        """
        Initialize sync status panel.
        
        Args:
            master: Parent widget
            cloud_manager: CloudStorageManager instance
            **kwargs: Additional CTkFrame arguments
        """
        super().__init__(master, **kwargs)
        self.cloud_manager = cloud_manager
        self._create_widgets()

    def _create_widgets(self) -> None:
        """Create sync status widgets."""
        ctk.CTkLabel(
            self,
            text="Sync Status",
            font=ctk.CTkFont(size=12, weight="bold"),
        ).pack(pady=5)

        # Offline mode toggle
        self.offline_var = ctk.BooleanVar(value=False)
        offline_check = ctk.CTkCheckBox(
            self,
            text="Offline Mode (Queue operations)",
            variable=self.offline_var,
            command=self._toggle_offline,
        )
        offline_check.pack(pady=5)

        # Sync queue
        queue_frame = ctk.CTkFrame(self)
        queue_frame.pack(fill="both", expand=True, padx=10, pady=10)

        ctk.CTkLabel(queue_frame, text="Sync Queue:").pack(pady=5)
        self.queue_listbox = ctk.CTkTextbox(queue_frame, height=200)
        self.queue_listbox.pack(fill="both", expand=True)

        # Refresh button
        ctk.CTkButton(
            self,
            text="Refresh",
            command=self._refresh_queue,
            width=100,
        ).pack(pady=5)

    def _toggle_offline(self) -> None:
        """Toggle offline mode."""
        self.cloud_manager.offline_mode = self.offline_var.get()
        if self.cloud_manager.offline_mode:
            self.cloud_manager.start_sync_worker()
        else:
            self.cloud_manager.stop_sync_worker()

    def _refresh_queue(self) -> None:
        """Refresh sync queue display."""
        self.queue_listbox.delete("1.0", "end")

        tasks = list(self.cloud_manager.sync_tasks.values())
        if not tasks:
            self.queue_listbox.insert("1.0", "No sync tasks")
            return

        for task in tasks[-10:]:  # Last 10 tasks
            self.queue_listbox.insert(
                "end",
                f"{task.operation.upper()}: {task.file_id}\n"
                f"   Status: {task.status.value}\n"
                f"   {task.error or ''}\n\n"
            )

