"""
Example usage of the Settings Manager.

This file demonstrates how to use the configuration system
in the MarkItDown GUI application.
"""

from pathlib import Path
from gui.config import (
    SettingsManager,
    Profile,
    Theme,
    Language,
    FileFormat,
    FileFormatConfig,
    ThemeConfig,
)


def example_basic_usage():
    """Basic usage example."""
    print("=== Basic Usage ===")
    
    # Initialize settings manager
    manager = SettingsManager()
    
    # Get current settings
    settings = manager.get()
    print(f"Current theme: {settings.ui.theme}")
    print(f"Current language: {settings.ui.language}")
    print(f"Plugins enabled: {settings.conversion.enable_plugins}")

    # Update settings
    manager.update(ui__theme="dark")
    manager.update(conversion__enable_plugins=True)
    
    # Save settings
    manager.save()
    print("Settings updated and saved!")


def example_profile_usage():
    """Profile management example."""
    print("\n=== Profile Management ===")
    
    # Initialize with development profile
    manager = SettingsManager(profile=Profile.DEVELOPMENT)
    settings = manager.get()
    print(f"Profile: {settings.profile}")
    print(f"Debug mode: {settings.advanced.enable_debug_mode}")
    print(f"Log level: {settings.advanced.log_level}")
    
    # Switch to production
    manager.set_profile(Profile.PRODUCTION)
    settings = manager.get()
    print(f"Switched to profile: {settings.profile}")


def example_file_format_config():
    """File format configuration example."""
    print("\n=== File Format Configuration ===")
    
    manager = SettingsManager()
    settings = manager.get()
    
    # Configure PDF settings
    pdf_config = FileFormatConfig(
        format=FileFormat.PDF,
        enabled=True,
        options={
            "ocr_enabled": True,
            "extract_tables": True,
            "extract_images": True,
        },
        max_file_size_mb=200,
        timeout_seconds=600,
    )
    
    settings.file_formats["pdf"] = pdf_config
    manager.save(settings)
    
    # Retrieve and use config
    pdf_config = manager.get_file_format_config("pdf")
    if pdf_config and pdf_config.enabled:
        print(f"PDF max size: {pdf_config.max_file_size_mb} MB")
        print(f"PDF OCR enabled: {pdf_config.options.get('ocr_enabled', False)}")


def example_theme_config():
    """Theme configuration example."""
    print("\n=== Theme Configuration ===")
    
    manager = SettingsManager()
    settings = manager.get()
    
    # Create custom theme
    custom_theme = ThemeConfig(
        name="custom",
        display_name="My Custom Theme",
        colors={
            "background": "#2C3E50",
            "foreground": "#ECF0F1",
            "primary": "#3498DB",
            "secondary": "#95A5A6",
            "success": "#2ECC71",
            "warning": "#F39C12",
            "error": "#E74C3C",
        },
        fonts={
            "default": "Arial",
            "monospace": "Courier New",
        },
        styles={
            "border_radius": 8,
            "padding": 10,
        },
    )
    
    settings.themes["custom"] = custom_theme
    settings.ui.theme = Theme.CUSTOM
    manager.save(settings)
    
    # Apply theme
    theme_config = manager.get_theme_config("custom")
    if theme_config:
        print(f"Theme: {theme_config.display_name}")
        print(f"Background: {theme_config.colors['background']}")
        print(f"Primary: {theme_config.colors['primary']}")


def example_i18n():
    """Internationalization example."""
    print("\n=== Internationalization ===")
    
    manager = SettingsManager()
    settings = manager.get()
    
    # Change language
    settings.ui.language = Language.PORTUGUESE
    manager.save(settings)
    
    # Get translated strings
    convert_text = manager.get_i18n_string("ui.convert_button")
    cancel_text = manager.get_i18n_string("ui.cancel_button")
    
    print(f"Convert button (PT): {convert_text}")
    print(f"Cancel button (PT): {cancel_text}")
    
    # Get in specific language
    convert_en = manager.get_i18n_string("ui.convert_button", Language.ENGLISH)
    convert_pt = manager.get_i18n_string("ui.convert_button", Language.PORTUGUESE)
    
    print(f"Convert (EN): {convert_en}")
    print(f"Convert (PT): {convert_pt}")


def example_hot_reload():
    """Hot reload example."""
    print("\n=== Hot Reload ===")
    
    manager = SettingsManager()
    
    def on_config_changed(new_settings):
        print(f"Configuration changed!")
        print(f"New theme: {new_settings.ui.theme}")
        print(f"New language: {new_settings.ui.language}")
    
    # Enable hot reload
    manager.enable_hot_reload(callback=on_config_changed)
    print("Hot reload enabled. Edit config.yaml to see changes.")
    print("Press Ctrl+C to stop...")
    
    try:
        import time
        time.sleep(10)  # Wait for changes
    except KeyboardInterrupt:
        pass
    finally:
        manager.disable_hot_reload()
        print("Hot reload disabled.")


def example_integration_with_app():
    """Example of integrating with the application."""
    print("\n=== Application Integration ===")
    
    from gui.core.app import create_app
    
    # Load settings
    manager = SettingsManager()
    settings = manager.get()
    
    # Create app with settings
    app = create_app(
        enable_plugins=settings.conversion.enable_plugins,
        docintel_endpoint=settings.conversion.docintel_endpoint,
        llm_model=settings.conversion.llm_model,
    )
    
    # Enable hot reload to update app when config changes
    def update_app_settings(new_settings):
        app.model.update_settings(
            enable_plugins=new_settings.conversion.enable_plugins,
            docintel_endpoint=new_settings.conversion.docintel_endpoint,
            llm_model=new_settings.conversion.llm_model,
        )
    
    manager.enable_hot_reload(callback=update_app_settings)
    
    print("Application initialized with settings")
    print("Hot reload enabled - config changes will update app")


if __name__ == "__main__":
    # Run examples
    example_basic_usage()
    example_profile_usage()
    example_file_format_config()
    example_theme_config()
    example_i18n()
    # example_hot_reload()  # Uncomment to test hot reload
    example_integration_with_app()

