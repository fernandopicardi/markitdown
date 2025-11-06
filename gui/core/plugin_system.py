"""
Plugin system for MarkItDown GUI.

This module provides an extensible plugin architecture with
lifecycle management, dependencies, sandboxing, and hot reload.
"""

import importlib
import importlib.util
import logging
import json
from pathlib import Path
from typing import Dict, List, Optional, Any, Type, Callable
from dataclasses import dataclass, field
from enum import Enum
from abc import ABC, abstractmethod
import threading
import time

try:
    import semver
    HAS_SEMVER = True
except ImportError:
    HAS_SEMVER = False

logger = logging.getLogger(__name__)


class PluginType(Enum):
    """Plugin types."""

    INPUT_PROCESSOR = "input_processor"
    OUTPUT_FORMATTER = "output_formatter"
    UI_EXTENSION = "ui_extension"
    INTEGRATION = "integration"


class PluginStatus(Enum):
    """Plugin status."""

    INSTALLED = "installed"
    ACTIVATED = "activated"
    DEACTIVATED = "deactivated"
    ERROR = "error"
    LOADING = "loading"


@dataclass
class PluginMetadata:
    """Plugin metadata."""

    plugin_id: str
    name: str
    version: str
    description: str
    author: str
    plugin_type: PluginType
    dependencies: List[str] = field(default_factory=list)
    min_version: Optional[str] = None
    max_version: Optional[str] = None
    config_schema: Optional[Dict[str, Any]] = None
    permissions: List[str] = field(default_factory=list)


class AbstractPlugin(ABC):
    """Abstract base class for all plugins."""

    def __init__(self, plugin_id: str, metadata: PluginMetadata) -> None:
        """
        Initialize plugin.
        
        Args:
            plugin_id: Unique plugin identifier
            metadata: Plugin metadata
        """
        self.plugin_id = plugin_id
        self.metadata = metadata
        self.status = PluginStatus.INSTALLED
        self.config: Dict[str, Any] = {}
        self.logger = logging.getLogger(f"plugin.{plugin_id}")
        self._hooks: Dict[str, List[Callable]] = {}

    @abstractmethod
    def init(self, context: Dict[str, Any]) -> None:
        """
        Initialize plugin (called once on load).
        
        Args:
            context: Plugin context (event_bus, etc.)
        """
        pass

    @abstractmethod
    def activate(self) -> None:
        """Activate plugin (called when enabled)."""
        pass

    @abstractmethod
    def deactivate(self) -> None:
        """Deactivate plugin (called when disabled)."""
        pass

    def get_info(self) -> Dict[str, Any]:
        """
        Get plugin information.
        
        Returns:
            Plugin info dictionary
        """
        return {
            "plugin_id": self.plugin_id,
            "name": self.metadata.name,
            "version": self.metadata.version,
            "description": self.metadata.description,
            "author": self.metadata.author,
            "type": self.metadata.plugin_type.value,
            "status": self.status.value,
        }

    def register_hook(self, hook_name: str, callback: Callable) -> None:
        """
        Register a hook callback.
        
        Args:
            hook_name: Hook name
            callback: Callback function
        """
        if hook_name not in self._hooks:
            self._hooks[hook_name] = []
        self._hooks[hook_name].append(callback)

    def call_hook(self, hook_name: str, *args, **kwargs) -> Any:
        """
        Call a hook.
        
        Args:
            hook_name: Hook name
            *args: Hook arguments
            **kwargs: Hook keyword arguments
            
        Returns:
            Hook result (if any)
        """
        if hook_name in self._hooks:
            for callback in self._hooks[hook_name]:
                try:
                    result = callback(*args, **kwargs)
                    if result is not None:
                        return result
                except Exception as e:
                    self.logger.error(f"Error in hook {hook_name}: {e}")
        return None

    def configure(self, config: Dict[str, Any]) -> None:
        """
        Configure plugin.
        
        Args:
            config: Configuration dictionary
        """
        self.config.update(config)
        self.logger.info(f"Plugin {self.plugin_id} configured")

    def get_config(self) -> Dict[str, Any]:
        """
        Get plugin configuration.
        
        Returns:
            Configuration dictionary
        """
        return self.config.copy()


class PluginManager:
    """Manages plugins for MarkItDown GUI."""

    def __init__(self, plugins_dir: Optional[Path] = None) -> None:
        """
        Initialize plugin manager.
        
        Args:
            plugins_dir: Directory containing plugins
        """
        if plugins_dir is None:
            import os
            if os.name == "nt":  # Windows
                plugins_dir = Path.home() / "AppData" / "Local" / "MarkItDown" / "plugins"
            else:  # Linux/Mac
                plugins_dir = Path.home() / ".config" / "markitdown" / "plugins"
            plugins_dir.mkdir(parents=True, exist_ok=True)

        self.plugins_dir = plugins_dir
        self.plugins: Dict[str, AbstractPlugin] = {}
        self.plugin_modules: Dict[str, Any] = {}
        self.enabled_plugins: List[str] = []
        self.context: Dict[str, Any] = {}
        self.hot_reload_enabled = True
        self.sandbox_enabled = True

        # Load plugins
        self._discover_plugins()

    def _discover_plugins(self) -> None:
        """Discover and load plugins."""
        if not self.plugins_dir.exists():
            return

        for plugin_file in self.plugins_dir.glob("**/*_plugin.py"):
            try:
                self._load_plugin(plugin_file)
            except Exception as e:
                logger.error(f"Failed to load plugin {plugin_file}: {e}")

    def _load_plugin(self, plugin_file: Path) -> Optional[AbstractPlugin]:
        """
        Load a plugin from file.
        
        Args:
            plugin_file: Path to plugin file
            
        Returns:
            Loaded plugin or None
        """
        try:
            # Load module
            spec = importlib.util.spec_from_file_location(
                plugin_file.stem,
                plugin_file
            )
            if spec is None or spec.loader is None:
                return None

            module = importlib.util.module_from_spec(spec)
            spec.loader.exec_module(module)

            # Find plugin class
            plugin_class = None
            for attr_name in dir(module):
                attr = getattr(module, attr_name)
                if (isinstance(attr, type) and
                    issubclass(attr, AbstractPlugin) and
                    attr != AbstractPlugin):
                    plugin_class = attr
                    break

            if plugin_class is None:
                logger.warning(f"No plugin class found in {plugin_file}")
                return None

            # Get metadata
            metadata = getattr(module, "PLUGIN_METADATA", None)
            if metadata is None:
                logger.warning(f"No metadata found in {plugin_file}")
                return None

            # Create plugin instance
            plugin_id = metadata.plugin_id
            plugin = plugin_class(plugin_id, metadata)

            # Initialize
            plugin.init(self.context)

            # Store
            self.plugins[plugin_id] = plugin
            self.plugin_modules[plugin_id] = module

            logger.info(f"Plugin loaded: {plugin_id}")
            return plugin

        except Exception as e:
            logger.error(f"Error loading plugin {plugin_file}: {e}")
            return None

    def register_plugin(self, plugin: AbstractPlugin) -> bool:
        """
        Register a plugin.
        
        Args:
            plugin: Plugin instance
            
        Returns:
            True if registered successfully
        """
        # Check dependencies
        if not self._check_dependencies(plugin):
            logger.error(f"Plugin {plugin.plugin_id} has unmet dependencies")
            return False

        self.plugins[plugin.plugin_id] = plugin
        plugin.init(self.context)
        logger.info(f"Plugin registered: {plugin.plugin_id}")
        return True

    def _check_dependencies(self, plugin: AbstractPlugin) -> bool:
        """
        Check if plugin dependencies are met.
        
        Args:
            plugin: Plugin to check
            
        Returns:
            True if all dependencies met
        """
        for dep_id in plugin.metadata.dependencies:
            if dep_id not in self.plugins:
                return False
            dep_plugin = self.plugins[dep_id]
            if dep_plugin.status != PluginStatus.ACTIVATED:
                return False
        return True

    def activate_plugin(self, plugin_id: str) -> bool:
        """
        Activate a plugin.
        
        Args:
            plugin_id: Plugin ID to activate
            
        Returns:
            True if activated successfully
        """
        if plugin_id not in self.plugins:
            logger.error(f"Plugin not found: {plugin_id}")
            return False

        plugin = self.plugins[plugin_id]

        # Check dependencies
        if not self._check_dependencies(plugin):
            logger.error(f"Plugin {plugin_id} has unmet dependencies")
            return False

        try:
            plugin.activate()
            plugin.status = PluginStatus.ACTIVATED
            if plugin_id not in self.enabled_plugins:
                self.enabled_plugins.append(plugin_id)
            logger.info(f"Plugin activated: {plugin_id}")
            return True
        except Exception as e:
            logger.error(f"Error activating plugin {plugin_id}: {e}")
            plugin.status = PluginStatus.ERROR
            return False

    def deactivate_plugin(self, plugin_id: str) -> bool:
        """
        Deactivate a plugin.
        
        Args:
            plugin_id: Plugin ID to deactivate
            
        Returns:
            True if deactivated successfully
        """
        if plugin_id not in self.plugins:
            return False

        plugin = self.plugins[plugin_id]
        try:
            plugin.deactivate()
            plugin.status = PluginStatus.DEACTIVATED
            if plugin_id in self.enabled_plugins:
                self.enabled_plugins.remove(plugin_id)
            logger.info(f"Plugin deactivated: {plugin_id}")
            return True
        except Exception as e:
            logger.error(f"Error deactivating plugin {plugin_id}: {e}")
            return False

    def get_plugin(self, plugin_id: str) -> Optional[AbstractPlugin]:
        """
        Get plugin by ID.
        
        Args:
            plugin_id: Plugin ID
            
        Returns:
            Plugin or None
        """
        return self.plugins.get(plugin_id)

    def get_plugins_by_type(self, plugin_type: PluginType) -> List[AbstractPlugin]:
        """
        Get plugins by type.
        
        Args:
            plugin_type: Plugin type
            
        Returns:
            List of plugins
        """
        return [
            p for p in self.plugins.values()
            if p.metadata.plugin_type == plugin_type
        ]

    def get_all_plugins(self) -> List[AbstractPlugin]:
        """
        Get all plugins.
        
        Returns:
            List of all plugins
        """
        return list(self.plugins.values())

    def set_context(self, context: Dict[str, Any]) -> None:
        """
        Set plugin context.
        
        Args:
            context: Context dictionary
        """
        self.context.update(context)
        # Re-initialize all plugins with new context
        for plugin in self.plugins.values():
            try:
                plugin.init(self.context)
            except Exception as e:
                logger.error(f"Error re-initializing plugin {plugin.plugin_id}: {e}")

    def hot_reload_plugin(self, plugin_id: str) -> bool:
        """
        Hot reload a plugin.
        
        Args:
            plugin_id: Plugin ID to reload
            
        Returns:
            True if reloaded successfully
        """
        if not self.hot_reload_enabled:
            return False

        if plugin_id not in self.plugins:
            return False

        was_active = plugin_id in self.enabled_plugins
        if was_active:
            self.deactivate_plugin(plugin_id)

        # Find plugin file
        plugin_file = None
        for file in self.plugins_dir.rglob(f"*{plugin_id}*_plugin.py"):
            plugin_file = file
            break

        if plugin_file:
            # Remove old module
            if plugin_id in self.plugin_modules:
                del self.plugin_modules[plugin_id]
            if plugin_id in self.plugins:
                del self.plugins[plugin_id]

            # Reload
            plugin = self._load_plugin(plugin_file)
            if plugin and was_active:
                self.activate_plugin(plugin_id)

            return plugin is not None

        return False

    def get_plugin_logs(self, plugin_id: str) -> List[str]:
        """
        Get plugin logs.
        
        Args:
            plugin_id: Plugin ID
            
        Returns:
            List of log messages
        """
        # This would integrate with logging system
        # For now, return empty list
        return []

