# Plugin System

## Overview

The MarkItDown GUI features an extensible plugin system that allows adding new functionality through plugins. The system supports lifecycle management, dependencies, sandboxing, versioning, hot reload, and automatic documentation.

## Features

### ✅ Plugin API Base
- **AbstractPlugin**: Base class for all plugins
- **Lifecycle Hooks**: init, activate, deactivate
- **Plugin Registration**: Automatic discovery and registration
- **Dependency System**: Plugin dependencies management

### ✅ Plugin Manager GUI
- **Plugin Listing**: List all installed plugins
- **Install/Uninstall**: Manage plugin installation
- **Activate/Deactivate**: Enable/disable plugins
- **Configuration**: Configure plugin settings
- **Local Marketplace**: Browse available plugins

### ✅ Plugin Types
- **Input Processors**: New input formats
- **Output Formatters**: Post-processing
- **UI Extensions**: New UI panels
- **Integrations**: External service integrations

### ✅ Sandboxing
- **Permission System**: Plugin permissions
- **Isolated Execution**: Safe plugin execution
- **Resource Limits**: Control plugin resources

### ✅ Versioning
- **Semantic Versioning**: Version comparison
- **Version Constraints**: Min/max version support
- **Compatibility Checking**: Automatic compatibility checks

### ✅ Hot Reload
- **Live Reload**: Reload plugins without restart
- **State Preservation**: Maintain plugin state
- **Error Recovery**: Handle reload errors

### ✅ Plugin Logs
- **Per-Plugin Logging**: Individual plugin logs
- **Log Viewing**: View plugin logs in UI
- **Error Tracking**: Track plugin errors

### ✅ Automatic Documentation
- **Metadata Extraction**: Extract plugin metadata
- **API Documentation**: Auto-generate docs
- **Usage Examples**: Plugin usage examples

## Plugin API

### Creating a Plugin

```python
from gui.core.plugin_system import (
    AbstractPlugin,
    PluginMetadata,
    PluginType,
)

PLUGIN_METADATA = PluginMetadata(
    plugin_id="my_plugin",
    name="My Plugin",
    version="1.0.0",
    description="Plugin description",
    author="Your Name",
    plugin_type=PluginType.INPUT_PROCESSOR,
    dependencies=[],
    config_schema={
        "setting1": {"type": "string", "default": "value"},
    },
    permissions=["file_read"],
)

class MyPlugin(AbstractPlugin):
    def init(self, context):
        """Initialize plugin."""
        self.event_bus = context.get("event_bus")
        
    def activate(self):
        """Activate plugin."""
        self.logger.info("Plugin activated")
        
    def deactivate(self):
        """Deactivate plugin."""
        self.logger.info("Plugin deactivated")
```

### Plugin Lifecycle

1. **Init**: Called once when plugin is loaded
2. **Activate**: Called when plugin is enabled
3. **Deactivate**: Called when plugin is disabled

### Plugin Types

#### Input Processor
```python
plugin_type=PluginType.INPUT_PROCESSOR
```
- Process new input formats
- Extend conversion capabilities
- Example: OCR plugin

#### Output Formatter
```python
plugin_type=PluginType.OUTPUT_FORMATTER
```
- Post-process output
- Format conversions
- Example: HTML formatter

#### UI Extension
```python
plugin_type=PluginType.UI_EXTENSION
```
- Add UI panels
- Extend interface
- Example: Custom viewer

#### Integration
```python
plugin_type=PluginType.INTEGRATION
```
- External services
- API integrations
- Example: Notion, Git

## Example Plugins

### OCR Plugin

```python
from gui.plugins.ocr_plugin import OCRPlugin

# Use OCR plugin
plugin = plugin_manager.get_plugin("ocr_advanced")
if plugin and plugin.status == PluginStatus.ACTIVATED:
    text = plugin.extract_text_from_image(image_path)
```

### Notion Export Plugin

```python
from gui.plugins.notion_plugin import NotionPlugin

# Export to Notion
plugin = plugin_manager.get_plugin("notion_export")
if plugin and plugin.status == PluginStatus.ACTIVATED:
    page_id = plugin.export_to_notion(markdown_text, "Page Title")
```

### Git Integration Plugin

```python
from gui.plugins.git_plugin import GitPlugin

# Commit conversion
plugin = plugin_manager.get_plugin("git_integration")
if plugin and plugin.status == PluginStatus.ACTIVATED:
    plugin.commit_conversion(original_file, markdown_file)
```

## Plugin Manager

### Using PluginManager

```python
from gui.core.plugin_system import PluginManager

# Create manager
manager = PluginManager()

# Set context
manager.set_context({
    "event_bus": event_bus,
    "conversion_model": conversion_model,
})

# Activate plugin
manager.activate_plugin("ocr_advanced")

# Get plugin
plugin = manager.get_plugin("ocr_advanced")

# Get plugins by type
input_plugins = manager.get_plugins_by_type(PluginType.INPUT_PROCESSOR)
```

### Plugin Management Window

```python
from gui.views.plugin_window import show_plugin_manager

# Show plugin manager
show_plugin_manager(plugin_manager)
```

## Plugin Configuration

### Config Schema

```python
config_schema = {
    "setting1": {
        "type": "string",
        "default": "default_value",
        "description": "Setting description"
    },
    "setting2": {
        "type": "integer",
        "default": 10,
        "min": 0,
        "max": 100
    },
    "secret": {
        "type": "string",
        "default": "",
        "secret": True  # Hidden in UI
    }
}
```

### Configuring Plugin

```python
# Configure plugin
plugin.configure({
    "setting1": "new_value",
    "setting2": 20
})

# Get configuration
config = plugin.get_config()
```

## Dependencies

### Declaring Dependencies

```python
PLUGIN_METADATA = PluginMetadata(
    plugin_id="dependent_plugin",
    dependencies=["required_plugin_id"],
    ...
)
```

### Dependency Checking

- Dependencies must be installed
- Dependencies must be activated
- Version constraints checked

## Versioning

### Version Format

- Semantic versioning: `MAJOR.MINOR.PATCH`
- Example: `1.2.3`

### Version Constraints

```python
PLUGIN_METADATA = PluginMetadata(
    min_version="1.0.0",
    max_version="2.0.0",
    ...
)
```

## Hot Reload

### Reloading Plugin

```python
# Hot reload plugin
manager.hot_reload_plugin("plugin_id")
```

### Reload Behavior

- Plugin is deactivated
- Module is reloaded
- Plugin is reactivated (if was active)
- State is preserved

## Logging

### Plugin Logs

```python
# Get plugin logs
logs = manager.get_plugin_logs("plugin_id")

# Plugin logger
self.logger.info("Plugin message")
self.logger.error("Plugin error")
```

## Permissions

### Permission Types

- `file_read`: Read files
- `file_write`: Write files
- `network_access`: Network operations
- `image_processing`: Image operations
- `git_operations`: Git operations
- `notion_write`: Notion API access

### Permission Checking

Plugins declare required permissions in metadata. The system checks permissions before activation.

## Sandboxing

### Sandbox Features

- Permission-based access control
- Resource limits
- Isolated execution
- Error isolation

## Best Practices

1. **Use Metadata**: Always define PLUGIN_METADATA
2. **Handle Errors**: Proper error handling
3. **Logging**: Use plugin logger
4. **Configuration**: Use config schema
5. **Dependencies**: Declare dependencies
6. **Versioning**: Use semantic versioning
7. **Testing**: Test plugins thoroughly
8. **Documentation**: Document plugin usage

## Troubleshooting

### Plugin Not Loading
- Check plugin file format
- Verify PLUGIN_METADATA exists
- Check for syntax errors
- Verify plugin class extends AbstractPlugin

### Plugin Not Activating
- Check dependencies
- Verify permissions
- Check configuration
- Review plugin logs

### Hot Reload Fails
- Check for syntax errors
- Verify plugin structure
- Check for circular dependencies

## See Also

- [Plugin System API](../core/plugin_system.py)
- [Example Plugins](../plugins/)
- [Plugin Manager UI](../components/plugin_manager_ui.py)
- [Plugin Window](../views/plugin_window.py)

