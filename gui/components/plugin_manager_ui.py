"""
Plugin Manager UI component for MarkItDown GUI.
"""

import customtkinter as ctk
from tkinter import messagebox
from pathlib import Path
from typing import Optional, Callable, List
import logging

from gui.core.plugin_system import (
    PluginManager,
    AbstractPlugin,
    PluginType,
    PluginStatus,
)

logger = logging.getLogger(__name__)


class PluginListPanel(ctk.CTkFrame):
    """Panel for listing plugins."""

    def __init__(
        self,
        master: Any,
        plugin_manager: PluginManager,
        on_plugin_selected: Optional[Callable[[str], None]] = None,
        **kwargs
    ) -> None:
        """
        Initialize plugin list panel.
        
        Args:
            master: Parent widget
            plugin_manager: PluginManager instance
            on_plugin_selected: Callback when plugin is selected
            **kwargs: Additional CTkFrame arguments
        """
        super().__init__(master, **kwargs)
        self.plugin_manager = plugin_manager
        self.on_plugin_selected = on_plugin_selected
        self._create_widgets()
        self._refresh_list()

    def _create_widgets(self) -> None:
        """Create list widgets."""
        # Header
        header = ctk.CTkFrame(self)
        header.pack(fill="x", padx=10, pady=10)

        ctk.CTkLabel(
            header,
            text="Installed Plugins",
            font=ctk.CTkFont(size=14, weight="bold"),
        ).pack(side="left", padx=10)

        # Filter
        filter_frame = ctk.CTkFrame(header)
        filter_frame.pack(side="right", padx=10)

        ctk.CTkLabel(filter_frame, text="Type:").pack(side="left", padx=5)
        self.filter_var = ctk.StringVar(value="all")
        filter_menu = ctk.CTkOptionMenu(
            filter_frame,
            values=["all", "input_processor", "output_formatter", "ui_extension", "integration"],
            variable=self.filter_var,
            command=self._filter_plugins,
            width=150,
        )
        filter_menu.pack(side="left", padx=5)

        # Plugin list
        list_frame = ctk.CTkFrame(self)
        list_frame.pack(fill="both", expand=True, padx=10, pady=10)

        self.plugin_listbox = ctk.CTkTextbox(list_frame)
        self.plugin_listbox.pack(fill="both", expand=True)

        # Note: CTkTextbox doesn't support click events well
        # Selection would need custom implementation

    def _refresh_list(self) -> None:
        """Refresh plugin list."""
        self.plugin_listbox.delete("1.0", "end")

        filter_type = self.filter_var.get()
        plugins = self._get_filtered_plugins(filter_type)

        for plugin in plugins:
            status_icon = "✓" if plugin.status == PluginStatus.ACTIVATED else "○"
            self.plugin_listbox.insert(
                "end",
                f"{status_icon} {plugin.metadata.name} ({plugin.metadata.version})\n"
                f"   {plugin.metadata.description}\n"
                f"   Type: {plugin.metadata.plugin_type.value}\n"
                f"   Status: {plugin.status.value}\n\n"
            )

    def _get_filtered_plugins(self, filter_type: str) -> List[AbstractPlugin]:
        """Get filtered plugins."""
        if filter_type == "all":
            return self.plugin_manager.get_all_plugins()
        else:
            plugin_type = PluginType(filter_type)
            return self.plugin_manager.get_plugins_by_type(plugin_type)

    def _filter_plugins(self, filter_type: str) -> None:
        """Filter plugins by type."""
        self._refresh_list()

    def select_plugin(self, plugin_id: str) -> None:
        """
        Select a plugin.
        
        Args:
            plugin_id: Plugin ID to select
        """
        if self.on_plugin_selected:
            self.on_plugin_selected(plugin_id)


class PluginDetailsPanel(ctk.CTkFrame):
    """Panel for plugin details and configuration."""

    def __init__(
        self,
        master: Any,
        plugin_manager: PluginManager,
        **kwargs
    ) -> None:
        """
        Initialize plugin details panel.
        
        Args:
            master: Parent widget
            plugin_manager: PluginManager instance
            **kwargs: Additional CTkFrame arguments
        """
        super().__init__(master, **kwargs)
        self.plugin_manager = plugin_manager
        self.current_plugin: Optional[AbstractPlugin] = None
        self._create_widgets()

    def _create_widgets(self) -> None:
        """Create details widgets."""
        # Info section
        info_frame = ctk.CTkFrame(self)
        info_frame.pack(fill="x", padx=10, pady=10)

        ctk.CTkLabel(
            info_frame,
            text="Plugin Details",
            font=ctk.CTkFont(size=14, weight="bold"),
        ).pack(pady=5)

        self.info_text = ctk.CTkTextbox(info_frame, height=150)
        self.info_text.pack(fill="x", padx=10, pady=5)

        # Configuration section
        config_frame = ctk.CTkFrame(self)
        config_frame.pack(fill="both", expand=True, padx=10, pady=10)

        ctk.CTkLabel(
            config_frame,
            text="Configuration",
            font=ctk.CTkFont(size=12, weight="bold"),
        ).pack(pady=5)

        self.config_text = ctk.CTkTextbox(config_frame)
        self.config_text.pack(fill="both", expand=True, padx=10, pady=5)

        # Buttons
        button_frame = ctk.CTkFrame(self)
        button_frame.pack(fill="x", padx=10, pady=10)

        self.activate_button = ctk.CTkButton(
            button_frame,
            text="Activate",
            command=self._activate_plugin,
            width=100,
        )
        self.activate_button.pack(side="left", padx=5)

        self.deactivate_button = ctk.CTkButton(
            button_frame,
            text="Deactivate",
            command=self._deactivate_plugin,
            width=100,
        )
        self.deactivate_button.pack(side="left", padx=5)

        ctk.CTkButton(
            button_frame,
            text="Reload",
            command=self._reload_plugin,
            width=100,
        ).pack(side="left", padx=5)

        ctk.CTkButton(
            button_frame,
            text="Save Config",
            command=self._save_config,
            width=100,
        ).pack(side="left", padx=5)

    def show_plugin(self, plugin_id: str) -> None:
        """
        Show plugin details.
        
        Args:
            plugin_id: Plugin ID to show
        """
        plugin = self.plugin_manager.get_plugin(plugin_id)
        if not plugin:
            return

        self.current_plugin = plugin

        # Update info
        info = plugin.get_info()
        self.info_text.delete("1.0", "end")
        info_text = f"""Name: {info['name']}
Version: {info['version']}
Author: {info['author']}
Type: {info['type']}
Status: {info['status']}
Description: {plugin.metadata.description}
"""
        if plugin.metadata.dependencies:
            info_text += f"\nDependencies: {', '.join(plugin.metadata.dependencies)}"
        self.info_text.insert("1.0", info_text)

        # Update config
        config = plugin.get_config()
        self.config_text.delete("1.0", "end")
        import json
        self.config_text.insert("1.0", json.dumps(config, indent=2))

        # Update buttons
        is_active = plugin.status == PluginStatus.ACTIVATED
        self.activate_button.configure(state="normal" if not is_active else "disabled")
        self.deactivate_button.configure(state="normal" if is_active else "disabled")

    def _activate_plugin(self) -> None:
        """Activate current plugin."""
        if self.current_plugin:
            if self.plugin_manager.activate_plugin(self.current_plugin.plugin_id):
                messagebox.showinfo("Success", "Plugin activated!")
                self.show_plugin(self.current_plugin.plugin_id)
            else:
                messagebox.showerror("Error", "Failed to activate plugin")

    def _deactivate_plugin(self) -> None:
        """Deactivate current plugin."""
        if self.current_plugin:
            if self.plugin_manager.deactivate_plugin(self.current_plugin.plugin_id):
                messagebox.showinfo("Success", "Plugin deactivated!")
                self.show_plugin(self.current_plugin.plugin_id)
            else:
                messagebox.showerror("Error", "Failed to deactivate plugin")

    def _reload_plugin(self) -> None:
        """Reload current plugin."""
        if self.current_plugin:
            if self.plugin_manager.hot_reload_plugin(self.current_plugin.plugin_id):
                messagebox.showinfo("Success", "Plugin reloaded!")
                self.show_plugin(self.current_plugin.plugin_id)
            else:
                messagebox.showerror("Error", "Failed to reload plugin")

    def _save_config(self) -> None:
        """Save plugin configuration."""
        if not self.current_plugin:
            return

        try:
            config_text = self.config_text.get("1.0", "end-1c")
            import json
            config = json.loads(config_text)
            self.current_plugin.configure(config)
            messagebox.showinfo("Success", "Configuration saved!")
        except Exception as e:
            messagebox.showerror("Error", f"Invalid configuration: {e}")


class PluginMarketplacePanel(ctk.CTkFrame):
    """Panel for local plugin marketplace."""

    def __init__(
        self,
        master: Any,
        plugin_manager: PluginManager,
        **kwargs
    ) -> None:
        """
        Initialize marketplace panel.
        
        Args:
            master: Parent widget
            plugin_manager: PluginManager instance
            **kwargs: Additional CTkFrame arguments
        """
        super().__init__(master, **kwargs)
        self.plugin_manager = plugin_manager
        self._create_widgets()

    def _create_widgets(self) -> None:
        """Create marketplace widgets."""
        ctk.CTkLabel(
            self,
            text="Plugin Marketplace (Local)",
            font=ctk.CTkFont(size=14, weight="bold"),
        ).pack(pady=10)

        # Marketplace list
        marketplace_frame = ctk.CTkFrame(self)
        marketplace_frame.pack(fill="both", expand=True, padx=10, pady=10)

        self.marketplace_listbox = ctk.CTkTextbox(marketplace_frame)
        self.marketplace_listbox.pack(fill="both", expand=True)

        # Load available plugins
        self._load_marketplace()

    def _load_marketplace(self) -> None:
        """Load available plugins from marketplace."""
        self.marketplace_listbox.delete("1.0", "end")

        # List plugins in plugins directory
        plugins_dir = self.plugin_manager.plugins_dir
        if plugins_dir.exists():
            plugin_files = list(plugins_dir.glob("**/*_plugin.py"))
            for plugin_file in plugin_files:
                self.marketplace_listbox.insert(
                    "end",
                    f"📦 {plugin_file.stem}\n"
                    f"   Path: {plugin_file}\n\n"
                )

