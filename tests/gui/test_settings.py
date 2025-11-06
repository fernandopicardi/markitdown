"""
Tests for the settings system.
"""

import pytest
import tempfile
import yaml
from pathlib import Path
from gui.config.settings import (
    SettingsManager,
    AppSettings,
    ConversionSettings,
    UISettings,
    AdvancedSettings,
    FileFormatConfig,
    ThemeConfig,
    Profile,
    Theme,
    Language,
    FileFormat,
)


@pytest.fixture
def temp_config_dir():
    """Create a temporary configuration directory."""
    with tempfile.TemporaryDirectory() as tmpdir:
        yield Path(tmpdir)


@pytest.fixture
def default_config_file(temp_config_dir):
    """Create a default config file."""
    config_file = temp_config_dir / "config.default.yaml"
    default_config = {
        "profile": "production",
        "conversion": {
            "enable_plugins": False,
            "auto_save": True,
        },
        "ui": {
            "theme": "default",
            "language": "en",
            "window_width": 800,
            "window_height": 600,
        },
        "advanced": {
            "log_level": "INFO",
            "cache_enabled": True,
        },
        "file_formats": {},
        "themes": {},
        "i18n": {},
    }
    with open(config_file, "w", encoding="utf-8") as f:
        yaml.dump(default_config, f)
    return config_file


def test_settings_manager_initialization(temp_config_dir, default_config_file):
    """Test SettingsManager initialization."""
    manager = SettingsManager(config_dir=temp_config_dir)
    settings = manager.get()
    assert settings is not None
    assert isinstance(settings, AppSettings)


def test_settings_loading(temp_config_dir, default_config_file):
    """Test loading settings from file."""
    manager = SettingsManager(config_dir=temp_config_dir)
    settings = manager.get()
    
    assert settings.profile == Profile.PRODUCTION
    assert settings.conversion.auto_save is True
    assert settings.ui.theme == Theme.DEFAULT
    assert settings.ui.window_width == 800


def test_settings_saving(temp_config_dir, default_config_file):
    """Test saving settings."""
    manager = SettingsManager(config_dir=temp_config_dir)
    settings = manager.get()
    
    # Modify settings
    settings.ui.theme = Theme.DARK
    settings.ui.language = Language.PORTUGUESE
    
    # Save
    manager.save(settings)
    
    # Reload and verify
    manager.load()
    new_settings = manager.get()
    assert new_settings.ui.theme == Theme.DARK
    assert new_settings.ui.language == Language.PORTUGUESE


def test_settings_update(temp_config_dir, default_config_file):
    """Test updating settings."""
    manager = SettingsManager(config_dir=temp_config_file.parent)
    
    manager.update(ui__theme="dark")
    manager.update(conversion__enable_plugins=True)
    
    settings = manager.get()
    assert settings.ui.theme == Theme.DARK
    assert settings.conversion.enable_plugins is True


def test_profile_switching(temp_config_dir, default_config_file):
    """Test switching profiles."""
    # Create profile-specific config
    dev_config = temp_config_dir / "config.development.yaml"
    dev_data = {
        "profile": "development",
        "advanced": {"log_level": "DEBUG"},
    }
    with open(dev_config, "w", encoding="utf-8") as f:
        yaml.dump(dev_data, f)
    
    manager = SettingsManager(config_dir=temp_config_dir, profile=Profile.DEVELOPMENT)
    settings = manager.get()
    
    assert settings.profile == Profile.DEVELOPMENT
    assert settings.advanced.log_level == "DEBUG"


def test_file_format_config(temp_config_dir, default_config_file):
    """Test file format configuration."""
    manager = SettingsManager(config_dir=temp_config_dir)
    settings = manager.get()
    
    # Add file format config
    pdf_config = FileFormatConfig(
        format=FileFormat.PDF,
        enabled=True,
        options={"ocr_enabled": True},
        max_file_size_mb=200,
    )
    settings.file_formats["pdf"] = pdf_config
    manager.save(settings)
    
    # Retrieve config
    retrieved_config = manager.get_file_format_config("pdf")
    assert retrieved_config is not None
    assert retrieved_config.format == FileFormat.PDF
    assert retrieved_config.enabled is True
    assert retrieved_config.options["ocr_enabled"] is True


def test_theme_config(temp_config_dir, default_config_file):
    """Test theme configuration."""
    manager = SettingsManager(config_dir=temp_config_dir)
    settings = manager.get()
    
    # Add theme config
    dark_theme = ThemeConfig(
        name="dark",
        display_name="Dark Theme",
        colors={"background": "#1E1E1E", "foreground": "#FFFFFF"},
        fonts={"default": "Segoe UI"},
    )
    settings.themes["dark"] = dark_theme
    manager.save(settings)
    
    # Retrieve theme
    retrieved_theme = manager.get_theme_config("dark")
    assert retrieved_theme is not None
    assert retrieved_theme.name == "dark"
    assert retrieved_theme.colors["background"] == "#1E1E1E"


def test_i18n_strings(temp_config_dir, default_config_file):
    """Test internationalization."""
    manager = SettingsManager(config_dir=temp_config_dir)
    settings = manager.get()
    
    # Add i18n data
    settings.i18n["en"] = {"ui": {"convert_button": "Convert"}}
    settings.i18n["pt"] = {"ui": {"convert_button": "Converter"}}
    manager.save(settings)
    
    # Get strings
    en_text = manager.get_i18n_string("ui.convert_button", Language.ENGLISH)
    pt_text = manager.get_i18n_string("ui.convert_button", Language.PORTUGUESE)
    
    assert en_text == "Convert"
    assert pt_text == "Converter"


def test_settings_validation(temp_config_dir, default_config_file):
    """Test settings validation."""
    manager = SettingsManager(config_dir=temp_config_dir)
    
    # Test invalid window size
    with pytest.raises(ValueError):
        manager.update(ui__window_width=100)  # Too small
    
    # Test invalid font size
    with pytest.raises(ValueError):
        manager.update(ui__font_size=5)  # Too small
    
    # Test invalid log level
    with pytest.raises(ValueError):
        manager.update(advanced__log_level="INVALID")


def test_settings_merge(temp_config_dir, default_config_file):
    """Test merging settings from multiple files."""
    # Create user config
    user_config = temp_config_dir / "config.yaml"
    user_data = {
        "ui": {"theme": "dark"},
        "conversion": {"enable_plugins": True},
    }
    with open(user_config, "w", encoding="utf-8") as f:
        yaml.dump(user_data, f)
    
    manager = SettingsManager(config_dir=temp_config_dir)
    settings = manager.get()
    
    # User config should override defaults
    assert settings.ui.theme == Theme.DARK
    assert settings.conversion.enable_plugins is True
    # Other defaults should remain
    assert settings.ui.window_width == 800


def test_settings_to_dict(temp_config_dir, default_config_file):
    """Test converting settings to dictionary."""
    manager = SettingsManager(config_dir=temp_config_dir)
    settings = manager.get()
    
    settings_dict = settings.to_dict()
    assert isinstance(settings_dict, dict)
    assert "profile" in settings_dict
    assert "conversion" in settings_dict
    assert "ui" in settings_dict
    assert "advanced" in settings_dict


def test_settings_from_dict(temp_config_dir):
    """Test creating settings from dictionary."""
    config_dict = {
        "profile": "production",
        "conversion": {
            "enable_plugins": False,
            "auto_save": True,
        },
        "ui": {
            "theme": "default",
            "language": "en",
        },
        "advanced": {
            "log_level": "INFO",
        },
        "file_formats": {},
        "themes": {},
        "i18n": {},
    }
    
    settings = AppSettings.from_dict(config_dict)
    assert settings.profile == Profile.PRODUCTION
    assert settings.conversion.auto_save is True
    assert settings.ui.theme == Theme.DEFAULT


def test_settings_to_yaml(temp_config_dir, default_config_file):
    """Test converting settings to YAML."""
    manager = SettingsManager(config_dir=temp_config_dir)
    settings = manager.get()
    
    yaml_str = settings.to_yaml()
    assert isinstance(yaml_str, str)
    assert "profile" in yaml_str
    assert "conversion" in yaml_str


def test_settings_from_yaml(temp_config_dir):
    """Test creating settings from YAML."""
    yaml_content = """
profile: production
conversion:
  enable_plugins: false
  auto_save: true
ui:
  theme: default
  language: en
advanced:
  log_level: INFO
file_formats: {}
themes: {}
i18n: {}
"""
    
    settings = AppSettings.from_yaml(yaml_content)
    assert settings.profile == Profile.PRODUCTION
    assert settings.conversion.auto_save is True
    assert settings.ui.theme == Theme.DEFAULT

