"""
Plugin management window for MarkItDown GUI.

Features:
- Plugin listing and management
- Install/uninstall plugins
- Activate/deactivate plugins
- Configure plugins
- Local marketplace
- Hot reload
- Plugin logs
"""

import customtkinter as ctk
from tkinter import filedialog, messagebox
from pathlib import Path
from typing import Optional
import logging

from gui.core.plugin_system import PluginManager
from gui.components.plugin_manager_ui import (
    PluginListPanel,
    PluginDetailsPanel,
    PluginMarketplacePanel,
)

logger = logging.getLogger(__name__)


class PluginManagementWindow(ctk.CTk):
    """Main window for plugin management."""

    def __init__(
        self,
        plugin_manager: Optional[PluginManager] = None,
        **kwargs
    ) -> None:
        """
        Initialize plugin management window.
        
        Args:
            plugin_manager: PluginManager instance (creates new if None)
            **kwargs: Additional CTk arguments
        """
        super().__init__(**kwargs)
        self.plugin_manager = plugin_manager or PluginManager()
        self.selected_plugin_id: Optional[str] = None

        self._setup_window()
        self._create_layout()

        logger.info("Plugin management window initialized")

    def _setup_window(self) -> None:
        """Configure window properties."""
        self.title("MarkItDown - Plugin Management")
        self.geometry("1400x900")
        self.minsize(1200, 700)

    def _create_layout(self) -> None:
        """Create main layout."""
        # Top toolbar
        toolbar = ctk.CTkFrame(self)
        toolbar.pack(fill="x", padx=10, pady=10)

        ctk.CTkLabel(
            toolbar,
            text="Plugin System",
            font=ctk.CTkFont(size=18, weight="bold"),
        ).pack(side="left", padx=10)

        # Buttons
        button_frame = ctk.CTkFrame(toolbar)
        button_frame.pack(side="right", padx=10)

        ctk.CTkButton(
            button_frame,
            text="Install Plugin",
            command=self._install_plugin,
            width=120,
        ).pack(side="left", padx=5)

        ctk.CTkButton(
            button_frame,
            text="Refresh",
            command=self._refresh_plugins,
            width=100,
        ).pack(side="left", padx=5)

        # Main content area
        main_frame = ctk.CTkFrame(self)
        main_frame.pack(fill="both", expand=True, padx=10, pady=10)

        # Left: Plugin list
        left_frame = ctk.CTkFrame(main_frame)
        left_frame.pack(side="left", fill="both", expand=False, padx=5)

        self.plugin_list = PluginListPanel(
            left_frame,
            self.plugin_manager,
            on_plugin_selected=self._on_plugin_selected,
        )
        self.plugin_list.pack(fill="both", expand=True)

        # Right: Details and marketplace
        right_frame = ctk.CTkFrame(main_frame)
        right_frame.pack(side="right", fill="both", expand=True, padx=5)

        # Tab view
        self.tabs = ctk.CTkTabview(right_frame)
        self.tabs.pack(fill="both", expand=True)

        # Details tab
        details_tab = self.tabs.add("Details")
        self.details_panel = PluginDetailsPanel(
            details_tab,
            self.plugin_manager,
        )
        self.details_panel.pack(fill="both", expand=True)

        # Marketplace tab
        marketplace_tab = self.tabs.add("Marketplace")
        self.marketplace_panel = PluginMarketplacePanel(
            marketplace_tab,
            self.plugin_manager,
        )
        self.marketplace_panel.pack(fill="both", expand=True)

        # Logs tab
        logs_tab = self.tabs.add("Logs")
        self._create_logs_view(logs_tab)

    def _create_logs_view(self, parent: ctk.CTkFrame) -> None:
        """Create logs view."""
        ctk.CTkLabel(
            parent,
            text="Plugin Logs",
            font=ctk.CTkFont(size=14, weight="bold"),
        ).pack(pady=10)

        self.logs_text = ctk.CTkTextbox(parent)
        self.logs_text.pack(fill="both", expand=True, padx=10, pady=10)

        # Refresh logs button
        ctk.CTkButton(
            parent,
            text="Refresh Logs",
            command=self._refresh_logs,
            width=120,
        ).pack(pady=5)

    def _on_plugin_selected(self, plugin_id: str) -> None:
        """Handle plugin selection."""
        self.selected_plugin_id = plugin_id
        self.details_panel.show_plugin(plugin_id)
        self.tabs.set("Details")

    def _install_plugin(self) -> None:
        """Install plugin from file."""
        file_path = filedialog.askopenfilename(
            title="Install Plugin",
            filetypes=[("Python", "*.py"), ("All Files", "*.*")]
        )
        if file_path:
            try:
                # Copy to plugins directory
                plugin_file = Path(file_path)
                dest_file = self.plugin_manager.plugins_dir / plugin_file.name
                import shutil
                shutil.copy2(plugin_file, dest_file)

                # Reload plugin
                plugin = self.plugin_manager._load_plugin(dest_file)
                if plugin:
                    messagebox.showinfo("Success", f"Plugin {plugin.plugin_id} installed!")
                    self._refresh_plugins()
                else:
                    messagebox.showerror("Error", "Failed to load plugin")
            except Exception as e:
                messagebox.showerror("Error", f"Failed to install plugin: {e}")

    def _refresh_plugins(self) -> None:
        """Refresh plugin list."""
        self.plugin_manager._discover_plugins()
        self.plugin_list._refresh_list()
        if self.selected_plugin_id:
            self.details_panel.show_plugin(self.selected_plugin_id)

    def _refresh_logs(self) -> None:
        """Refresh plugin logs."""
        self.logs_text.delete("1.0", "end")

        # Collect logs from all plugins
        for plugin in self.plugin_manager.get_all_plugins():
            logs = self.plugin_manager.get_plugin_logs(plugin.plugin_id)
            if logs:
                self.logs_text.insert(
                    "end",
                    f"=== {plugin.metadata.name} ===\n"
                )
                for log in logs[-10:]:  # Last 10 logs
                    self.logs_text.insert("end", f"{log}\n")
                self.logs_text.insert("end", "\n")

    def set_context(self, context: dict) -> None:
        """
        Set plugin context.
        
        Args:
            context: Context dictionary
        """
        self.plugin_manager.set_context(context)

    def run(self) -> None:
        """Start the window."""
        logger.info("Starting plugin management window")
        self.mainloop()


def show_plugin_manager(plugin_manager: Optional[PluginManager] = None) -> None:
    """
    Show plugin management window.
    
    Args:
        plugin_manager: PluginManager instance (creates new if None)
    """
    window = PluginManagementWindow(plugin_manager=plugin_manager)
    window.run()

