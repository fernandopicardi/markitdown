# Configuration System Documentation

## Overview

The MarkItDown GUI uses a robust configuration system based on Pydantic for validation and YAML for persistence. The system supports:

- ✅ Profile-based configurations (development, production, test)
- ✅ Hot reload of configuration files
- ✅ File format-specific settings
- ✅ Customizable themes
- ✅ Internationalization (i18n) support
- ✅ Type-safe validation

## Configuration Files

### File Hierarchy

The configuration system loads settings in the following order (later files override earlier ones):

1. `config.default.yaml` - Default settings (included with application)
2. `config.yaml` - User-specific settings (in user config directory)
3. `config.{profile}.yaml` - Profile-specific settings (e.g., `config.development.yaml`)

### Configuration Directory

- **Windows**: `%LOCALAPPDATA%\MarkItDown\`
- **Linux/Mac**: `~/.config/markitdown/`

## Usage

### Basic Usage

```python
from gui.config import SettingsManager, Profile

# Initialize settings manager
settings_manager = SettingsManager()

# Get current settings
settings = settings_manager.get()

# Access settings
print(settings.ui.theme)
print(settings.conversion.enable_plugins)
print(settings.advanced.log_level)

# Update settings
settings_manager.update(ui__theme="dark")
settings_manager.update(conversion__enable_plugins=True)

# Save settings
settings_manager.save()
```

### Profile Management

```python
from gui.config import SettingsManager, Profile

# Initialize with specific profile
settings_manager = SettingsManager(profile=Profile.DEVELOPMENT)

# Switch profile
settings_manager.set_profile(Profile.PRODUCTION)

# Get profile-specific settings
settings = settings_manager.get()
print(f"Current profile: {settings.profile}")
```

### Hot Reload

```python
from gui.config import SettingsManager

settings_manager = SettingsManager()

def on_config_changed(new_settings):
    print("Configuration changed!")
    print(f"New theme: {new_settings.ui.theme}")

# Enable hot reload
settings_manager.enable_hot_reload(callback=on_config_changed)

# ... later, disable hot reload
settings_manager.disable_hot_reload()
```

### File Format Configuration

```python
from gui.config import SettingsManager

settings_manager = SettingsManager()
settings = settings_manager.get()

# Get format-specific config
pdf_config = settings_manager.get_file_format_config("pdf")
if pdf_config:
    print(f"PDF max size: {pdf_config.max_file_size_mb} MB")
    print(f"PDF options: {pdf_config.options}")

# Access in settings
pdf_config = settings.file_formats.get("pdf")
```

### Theme Configuration

```python
from gui.config import SettingsManager

settings_manager = SettingsManager()
settings = settings_manager.get()

# Get theme config
theme_config = settings_manager.get_theme_config("dark")
if theme_config:
    print(f"Theme colors: {theme_config.colors}")
    print(f"Theme fonts: {theme_config.fonts}")

# Access in settings
dark_theme = settings.themes.get("dark")
```

### Internationalization

```python
from gui.config import SettingsManager, Language

settings_manager = SettingsManager()
settings = settings_manager.get()

# Get translated string
convert_text = settings_manager.get_i18n_string("ui.convert_button")
# Returns text in current UI language

# Get string in specific language
convert_text_pt = settings_manager.get_i18n_string(
    "ui.convert_button",
    language=Language.PORTUGUESE
)
```

## Configuration Structure

### Conversion Settings

```yaml
conversion:
  enable_plugins: false
  docintel_endpoint: null
  docintel_key: null
  llm_enabled: false
  llm_model: null
  llm_api_key: null
  llm_prompt: null
  default_output_dir: null
  auto_save: true
  preserve_formatting: true
  max_concurrent_conversions: 1
```

### UI Settings

```yaml
ui:
  theme: default
  language: en
  window_width: 800
  window_height: 600
  window_maximized: false
  auto_save_geometry: true
  show_toolbar: true
  show_statusbar: true
  show_line_numbers: false
  font_family: "Segoe UI"
  font_size: 10
```

### Advanced Settings

```yaml
advanced:
  log_level: INFO
  log_file: null
  enable_debug_mode: false
  cache_enabled: true
  cache_size_mb: 100
  auto_update_check: true
  telemetry_enabled: false
  experimental_features: false
```

### File Format Configuration

```yaml
file_formats:
  pdf:
    format: pdf
    enabled: true
    options:
      extract_images: true
      extract_tables: true
      ocr_enabled: false
    max_file_size_mb: 100
    timeout_seconds: 300
```

### Theme Configuration

```yaml
themes:
  dark:
    name: dark
    display_name: Dark
    colors:
      background: "#1E1E1E"
      foreground: "#FFFFFF"
      primary: "#0078D4"
    fonts:
      default: "Segoe UI"
      monospace: "Consolas"
    styles:
      border_radius: 4
      padding: 8
```

### Internationalization

```yaml
i18n:
  en:
    ui:
      convert_button: "Convert"
      cancel_button: "Cancel"
  pt:
    ui:
      convert_button: "Converter"
      cancel_button: "Cancelar"
```

## Validation

All settings are validated using Pydantic:

- **Type checking**: Automatic type validation
- **Value ranges**: Window size, font size, cache size, etc.
- **Enum validation**: Profile, Theme, Language, FileFormat
- **Custom validators**: Log level, concurrent conversions, etc.

## Examples

### Example 1: Change Theme

```python
from gui.config import SettingsManager

settings_manager = SettingsManager()
settings_manager.update(ui__theme="dark")
settings_manager.save()
```

### Example 2: Enable Plugins

```python
from gui.config import SettingsManager

settings_manager = SettingsManager()
settings_manager.update(conversion__enable_plugins=True)
settings_manager.save()
```

### Example 3: Configure PDF Settings

```python
from gui.config import SettingsManager, FileFormatConfig, FileFormat

settings_manager = SettingsManager()
settings = settings_manager.get()

# Update PDF config
pdf_config = FileFormatConfig(
    format=FileFormat.PDF,
    enabled=True,
    options={"ocr_enabled": True, "extract_tables": True},
    max_file_size_mb=200,
    timeout_seconds=600
)

settings.file_formats["pdf"] = pdf_config
settings_manager.save(settings)
```

### Example 4: Add Custom Theme

```python
from gui.config import SettingsManager, ThemeConfig

settings_manager = SettingsManager()
settings = settings_manager.get()

custom_theme = ThemeConfig(
    name="custom",
    display_name="My Custom Theme",
    colors={
        "background": "#2C3E50",
        "foreground": "#ECF0F1",
        "primary": "#3498DB"
    },
    fonts={"default": "Arial", "monospace": "Courier New"},
    styles={"border_radius": 8, "padding": 10}
)

settings.themes["custom"] = custom_theme
settings.ui.theme = "custom"
settings_manager.save(settings)
```

### Example 5: Add Translation

```python
from gui.config import SettingsManager, Language

settings_manager = SettingsManager()
settings = settings_manager.get()

# Add custom translation
if "custom" not in settings.i18n:
    settings.i18n["custom"] = {}

settings.i18n["custom"]["ui"] = {
    "convert_button": "Custom Convert Text",
    "cancel_button": "Custom Cancel Text"
}

settings_manager.save(settings)
```

## Integration with Application

### In App Initialization

```python
from gui.core.app import create_app
from gui.config import SettingsManager

# Load settings
settings_manager = SettingsManager()
settings = settings_manager.get()

# Create app with settings
app = create_app(
    enable_plugins=settings.conversion.enable_plugins,
    docintel_endpoint=settings.conversion.docintel_endpoint,
    llm_client=None,  # Initialize from settings if needed
    llm_model=settings.conversion.llm_model
)

# Enable hot reload
settings_manager.enable_hot_reload(
    callback=lambda new_settings: app.update_settings(new_settings)
)
```

### In View Components

```python
from gui.config import SettingsManager

class MainWindow:
    def __init__(self):
        self.settings_manager = SettingsManager()
        self.settings = self.settings_manager.get()
        
        # Apply theme
        self._apply_theme(self.settings.ui.theme)
        
        # Apply language
        self._apply_language(self.settings.ui.language)
    
    def _apply_theme(self, theme_name: str):
        theme_config = self.settings_manager.get_theme_config(theme_name)
        if theme_config:
            # Apply colors, fonts, styles
            pass
    
    def _apply_language(self, language: str):
        # Update UI text
        convert_text = self.settings_manager.get_i18n_string("ui.convert_button")
        self.convert_button.config(text=convert_text)
```

## Best Practices

1. **Always use SettingsManager**: Don't access config files directly
2. **Validate before saving**: Settings are automatically validated
3. **Use profiles**: Use development profile for debugging
4. **Backup config**: SettingsManager creates backups automatically
5. **Hot reload**: Enable for development, disable for production
6. **Type safety**: Use type hints when accessing settings

## Troubleshooting

### Configuration not loading

- Check file paths and permissions
- Verify YAML syntax
- Check logs for validation errors

### Settings not applying

- Ensure `save()` is called after updates
- Check if profile-specific config is overriding
- Verify hot reload is working (if enabled)

### Validation errors

- Check Pydantic validation errors in logs
- Verify enum values (Profile, Theme, Language)
- Check value ranges (window size, font size, etc.)

## See Also

- `config.default.yaml` - Complete default configuration
- `config.yaml.example` - User configuration template
- `config.development.yaml` - Development profile example
- `config.test.yaml` - Test profile example

