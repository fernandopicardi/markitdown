"""
Settings management for MarkItDown GUI.

This module provides a robust configuration system using Pydantic
for validation and YAML for persistence.
"""

import yaml
import logging
from pathlib import Path
from typing import Optional, Dict, Any, List, Callable
from enum import Enum
from dataclasses import dataclass, field
from datetime import datetime
import json

try:
    from pydantic import BaseModel, Field, field_validator, model_validator
    from pydantic_settings import BaseSettings, SettingsConfigDict
except ImportError:
    # Fallback if Pydantic is not available
    BaseModel = object
    BaseSettings = object
    Field = lambda **kwargs: None
    field_validator = lambda *args, **kwargs: lambda f: f
    model_validator = lambda *args, **kwargs: lambda f: f
    SettingsConfigDict = dict

logger = logging.getLogger(__name__)


class Profile(str, Enum):
    """Application profiles."""

    DEVELOPMENT = "development"
    PRODUCTION = "production"
    TEST = "test"


class Theme(str, Enum):
    """Available UI themes."""

    DEFAULT = "default"
    DARK = "dark"
    LIGHT = "light"
    BLUE = "blue"
    GREEN = "green"
    CUSTOM = "custom"


class Language(str, Enum):
    """Supported languages for internationalization."""

    ENGLISH = "en"
    PORTUGUESE = "pt"
    SPANISH = "es"
    FRENCH = "fr"
    GERMAN = "de"
    JAPANESE = "ja"
    CHINESE = "zh"


class FileFormat(str, Enum):
    """Supported file formats."""

    PDF = "pdf"
    DOCX = "docx"
    PPTX = "pptx"
    XLSX = "xlsx"
    HTML = "html"
    CSV = "csv"
    JSON = "json"
    XML = "xml"
    IMAGE = "image"
    AUDIO = "audio"
    EPUB = "epub"
    ZIP = "zip"


@dataclass
class FileFormatConfig:
    """Configuration for a specific file format."""

    format: FileFormat
    enabled: bool = True
    options: Dict[str, Any] = field(default_factory=dict)
    custom_converter: Optional[str] = None
    max_file_size_mb: Optional[float] = None
    timeout_seconds: Optional[int] = None

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary."""
        return {
            "format": self.format.value,
            "enabled": self.enabled,
            "options": self.options,
            "custom_converter": self.custom_converter,
            "max_file_size_mb": self.max_file_size_mb,
            "timeout_seconds": self.timeout_seconds,
        }

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "FileFormatConfig":
        """Create from dictionary."""
        return cls(
            format=FileFormat(data.get("format", "pdf")),
            enabled=data.get("enabled", True),
            options=data.get("options", {}),
            custom_converter=data.get("custom_converter"),
            max_file_size_mb=data.get("max_file_size_mb"),
            timeout_seconds=data.get("timeout_seconds"),
        )


@dataclass
class ThemeConfig:
    """Theme configuration."""

    name: str
    display_name: str
    colors: Dict[str, str] = field(default_factory=dict)
    fonts: Dict[str, str] = field(default_factory=dict)
    styles: Dict[str, Any] = field(default_factory=dict)

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary."""
        return {
            "name": self.name,
            "display_name": self.display_name,
            "colors": self.colors,
            "fonts": self.fonts,
            "styles": self.styles,
        }

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "ThemeConfig":
        """Create from dictionary."""
        return cls(
            name=data.get("name", "default"),
            display_name=data.get("display_name", "Default"),
            colors=data.get("colors", {}),
            fonts=data.get("fonts", {}),
            styles=data.get("styles", {}),
        )


class ConversionSettings(BaseModel):
    """Settings for file conversion."""

    enable_plugins: bool = False
    docintel_endpoint: Optional[str] = None
    docintel_key: Optional[str] = None
    llm_enabled: bool = False
    llm_model: Optional[str] = None
    llm_api_key: Optional[str] = None
    llm_prompt: Optional[str] = None
    default_output_dir: Optional[str] = None
    auto_save: bool = True
    preserve_formatting: bool = True
    max_concurrent_conversions: int = 1

    @field_validator("max_concurrent_conversions")
    @classmethod
    def validate_concurrent(cls, v: int) -> int:
        """Validate concurrent conversions."""
        if v < 1:
            raise ValueError("max_concurrent_conversions must be at least 1")
        if v > 10:
            raise ValueError("max_concurrent_conversions cannot exceed 10")
        return v


class UISettings(BaseModel):
    """UI-related settings."""

    theme: Theme = Theme.DEFAULT
    language: Language = Language.ENGLISH
    window_width: int = 800
    window_height: int = 600
    window_maximized: bool = False
    show_toolbar: bool = True
    show_statusbar: bool = True
    show_line_numbers: bool = False
    font_family: str = "Segoe UI"
    font_size: int = 10
    auto_save_geometry: bool = True

    @field_validator("window_width", "window_height")
    @classmethod
    def validate_window_size(cls, v: int) -> int:
        """Validate window size."""
        if v < 400:
            raise ValueError("Window size must be at least 400 pixels")
        if v > 5000:
            raise ValueError("Window size cannot exceed 5000 pixels")
        return v

    @field_validator("font_size")
    @classmethod
    def validate_font_size(cls, v: int) -> int:
        """Validate font size."""
        if v < 8:
            raise ValueError("Font size must be at least 8")
        if v > 24:
            raise ValueError("Font size cannot exceed 24")
        return v


class AdvancedSettings(BaseModel):
    """Advanced application settings."""

    log_level: str = "INFO"
    log_file: Optional[str] = None
    enable_debug_mode: bool = False
    cache_enabled: bool = True
    cache_size_mb: int = 100
    auto_update_check: bool = True
    telemetry_enabled: bool = False
    experimental_features: bool = False

    @field_validator("log_level")
    @classmethod
    def validate_log_level(cls, v: str) -> str:
        """Validate log level."""
        valid_levels = ["DEBUG", "INFO", "WARNING", "ERROR", "CRITICAL"]
        if v.upper() not in valid_levels:
            raise ValueError(f"Log level must be one of {valid_levels}")
        return v.upper()

    @field_validator("cache_size_mb")
    @classmethod
    def validate_cache_size(cls, v: int) -> int:
        """Validate cache size."""
        if v < 0:
            raise ValueError("Cache size cannot be negative")
        if v > 1000:
            raise ValueError("Cache size cannot exceed 1000 MB")
        return v


class AppSettings(BaseModel):
    """Main application settings model."""

    profile: Profile = Profile.PRODUCTION
    conversion: ConversionSettings = Field(default_factory=ConversionSettings)
    ui: UISettings = Field(default_factory=UISettings)
    advanced: AdvancedSettings = Field(default_factory=AdvancedSettings)
    file_formats: Dict[str, FileFormatConfig] = Field(default_factory=dict)
    themes: Dict[str, ThemeConfig] = Field(default_factory=dict)
    i18n: Dict[str, Any] = Field(default_factory=dict)

    model_config = SettingsConfigDict(
        env_prefix="MARKITDOWN_",
        case_sensitive=False,
        extra="allow"
    )

    @model_validator(mode="after")
    def validate_settings(self) -> "AppSettings":
        """Validate settings after initialization."""
        # Validate file formats
        for format_name, format_config in self.file_formats.items():
            if not isinstance(format_config, FileFormatConfig):
                if isinstance(format_config, dict):
                    self.file_formats[format_name] = FileFormatConfig.from_dict(format_config)
                else:
                    raise ValueError(f"Invalid file format config for {format_name}")

        # Validate themes
        for theme_name, theme_config in self.themes.items():
            if not isinstance(theme_config, ThemeConfig):
                if isinstance(theme_config, dict):
                    self.themes[theme_name] = ThemeConfig.from_dict(theme_config)
                else:
                    raise ValueError(f"Invalid theme config for {theme_name}")

        return self

    def to_dict(self) -> Dict[str, Any]:
        """Convert settings to dictionary."""
        return {
            "profile": self.profile.value,
            "conversion": self.conversion.model_dump(),
            "ui": self.ui.model_dump(),
            "advanced": self.advanced.model_dump(),
            "file_formats": {
                k: v.to_dict() if isinstance(v, FileFormatConfig) else v
                for k, v in self.file_formats.items()
            },
            "themes": {
                k: v.to_dict() if isinstance(v, ThemeConfig) else v
                for k, v in self.themes.items()
            },
            "i18n": self.i18n,
        }

    def to_yaml(self) -> str:
        """Convert settings to YAML string."""
        return yaml.dump(self.to_dict(), default_flow_style=False, sort_keys=False)

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "AppSettings":
        """Create settings from dictionary."""
        # Convert file formats
        file_formats = {}
        if "file_formats" in data:
            for k, v in data["file_formats"].items():
                if isinstance(v, dict):
                    file_formats[k] = FileFormatConfig.from_dict(v)
                else:
                    file_formats[k] = v

        # Convert themes
        themes = {}
        if "themes" in data:
            for k, v in data["themes"].items():
                if isinstance(v, dict):
                    themes[k] = ThemeConfig.from_dict(v)
                else:
                    themes[k] = v

        return cls(
            profile=Profile(data.get("profile", "production")),
            conversion=ConversionSettings(**data.get("conversion", {})),
            ui=UISettings(**data.get("ui", {})),
            advanced=AdvancedSettings(**data.get("advanced", {})),
            file_formats=file_formats,
            themes=themes,
            i18n=data.get("i18n", {}),
        )

    @classmethod
    def from_yaml(cls, yaml_content: str) -> "AppSettings":
        """Create settings from YAML string."""
        data = yaml.safe_load(yaml_content)
        if not data:
            data = {}
        return cls.from_dict(data)


class SettingsManager:
    """
    Manages application settings with persistence and hot reload.
    
    This class handles loading, saving, and watching configuration files.
    """

    def __init__(
        self,
        config_dir: Optional[Path] = None,
        profile: Optional[Profile] = None
    ) -> None:
        """
        Initialize the settings manager.
        
        Args:
            config_dir: Directory for configuration files (defaults to user config dir)
            profile: Active profile (defaults to PRODUCTION)
        """
        if config_dir is None:
            # Use platform-specific config directory
            import os
            if os.name == "nt":  # Windows
                config_dir = Path.home() / "AppData" / "Local" / "MarkItDown"
            else:  # Linux/Mac
                config_dir = Path.home() / ".config" / "markitdown"
            config_dir.mkdir(parents=True, exist_ok=True)

        self.config_dir = config_dir
        self.profile = profile or Profile.PRODUCTION
        self.settings: Optional[AppSettings] = None
        self._watchers: List[Any] = []
        self._callbacks: List[Callable[[AppSettings], None]] = []
        self._last_modified: Optional[float] = None

        # File paths
        self.default_config_path = Path(__file__).parent / "config.default.yaml"
        self.user_config_path = self.config_dir / "config.yaml"
        self.profile_config_path = self.config_dir / f"config.{self.profile.value}.yaml"

        # Load settings
        self.load()

    def load(self) -> AppSettings:
        """
        Load settings from files.
        
        Priority:
        1. Profile-specific config (config.{profile}.yaml)
        2. User config (config.yaml)
        3. Default config (config.default.yaml)
        
        Returns:
            Loaded AppSettings instance
        """
        # Start with defaults
        default_settings = self._load_defaults()

        # Merge user config if exists
        if self.user_config_path.exists():
            try:
                user_settings = self._load_file(self.user_config_path)
                default_settings = self._merge_settings(default_settings, user_settings)
            except Exception as e:
                logger.warning(f"Failed to load user config: {e}")

        # Merge profile-specific config if exists
        if self.profile_config_path.exists():
            try:
                profile_settings = self._load_file(self.profile_config_path)
                default_settings = self._merge_settings(default_settings, profile_settings)
            except Exception as e:
                logger.warning(f"Failed to load profile config: {e}")

        self.settings = default_settings
        logger.info(f"Settings loaded for profile: {self.profile.value}")
        return self.settings

    def _load_defaults(self) -> AppSettings:
        """Load default settings."""
        if self.default_config_path.exists():
            return self._load_file(self.default_config_path)
        else:
            # Return minimal defaults
            return AppSettings()

    def _load_file(self, file_path: Path) -> AppSettings:
        """Load settings from a YAML file."""
        try:
            with open(file_path, "r", encoding="utf-8") as f:
                content = f.read()
            return AppSettings.from_yaml(content)
        except Exception as e:
            logger.error(f"Failed to load config file {file_path}: {e}")
            raise

    def _merge_settings(self, base: AppSettings, override: AppSettings) -> AppSettings:
        """Merge two settings objects, with override taking precedence."""
        base_dict = base.to_dict()
        override_dict = override.to_dict()

        # Deep merge
        merged_dict = self._deep_merge(base_dict, override_dict)
        return AppSettings.from_dict(merged_dict)

    def _deep_merge(self, base: Dict[str, Any], override: Dict[str, Any]) -> Dict[str, Any]:
        """Deep merge two dictionaries."""
        result = base.copy()
        for key, value in override.items():
            if key in result and isinstance(result[key], dict) and isinstance(value, dict):
                result[key] = self._deep_merge(result[key], value)
            else:
                result[key] = value
        return result

    def save(self, settings: Optional[AppSettings] = None) -> None:
        """
        Save settings to user config file.
        
        Args:
            settings: Settings to save (uses current if None)
        """
        if settings is None:
            settings = self.settings
        if settings is None:
            raise ValueError("No settings to save")

        try:
            # Create backup
            if self.user_config_path.exists():
                backup_path = self.user_config_path.with_suffix(".yaml.bak")
                import shutil
                shutil.copy2(self.user_config_path, backup_path)

            # Save settings
            with open(self.user_config_path, "w", encoding="utf-8") as f:
                f.write(settings.to_yaml())

            self.settings = settings
            self._last_modified = self.user_config_path.stat().st_mtime
            logger.info("Settings saved successfully")
        except Exception as e:
            logger.error(f"Failed to save settings: {e}")
            raise

    def get(self) -> AppSettings:
        """
        Get current settings.
        
        Returns:
            Current AppSettings instance
        """
        if self.settings is None:
            self.load()
        return self.settings

    def update(self, **kwargs: Any) -> None:
        """
        Update settings with new values.
        
        Args:
            **kwargs: Settings to update (nested keys supported with dots)
        """
        if self.settings is None:
            self.load()

        settings_dict = self.settings.to_dict()
        for key, value in kwargs.items():
            keys = key.split(".")
            target = settings_dict
            for k in keys[:-1]:
                if k not in target:
                    target[k] = {}
                target = target[k]
            target[keys[-1]] = value

        self.settings = AppSettings.from_dict(settings_dict)
        self.save()

    def enable_hot_reload(self, callback: Optional[Callable[[AppSettings], None]] = None) -> None:
        """
        Enable hot reload of configuration files.
        
        Args:
            callback: Optional callback function called when config changes
        """
        try:
            from watchdog.observers import Observer
            from watchdog.events import FileSystemEventHandler

            class ConfigHandler(FileSystemEventHandler):
                def __init__(self, manager: "SettingsManager", callback: Optional[Callable] = None):
                    self.manager = manager
                    self.callback = callback

                def on_modified(self, event):
                    if event.src_path.endswith(".yaml"):
                        logger.info("Configuration file changed, reloading...")
                        try:
                            self.manager.load()
                            if self.callback:
                                self.callback(self.manager.get())
                        except Exception as e:
                            logger.error(f"Failed to reload config: {e}")

            if callback:
                self._callbacks.append(callback)

            handler = ConfigHandler(self, callback)
            observer = Observer()
            observer.schedule(handler, str(self.config_dir), recursive=False)
            observer.start()

            self._watchers.append(observer)
            logger.info("Hot reload enabled for configuration files")
        except ImportError:
            logger.warning("watchdog not available, hot reload disabled")

    def disable_hot_reload(self) -> None:
        """Disable hot reload."""
        for watcher in self._watchers:
            watcher.stop()
            watcher.join()
        self._watchers.clear()
        logger.info("Hot reload disabled")

    def set_profile(self, profile: Profile) -> None:
        """
        Switch to a different profile.
        
        Args:
            profile: Profile to switch to
        """
        self.profile = profile
        self.profile_config_path = self.config_dir / f"config.{profile.value}.yaml"
        self.load()
        logger.info(f"Switched to profile: {profile.value}")

    def get_file_format_config(self, format_name: str) -> Optional[FileFormatConfig]:
        """
        Get configuration for a specific file format.
        
        Args:
            format_name: Name of the file format
            
        Returns:
            FileFormatConfig or None if not found
        """
        settings = self.get()
        return settings.file_formats.get(format_name)

    def get_theme_config(self, theme_name: str) -> Optional[ThemeConfig]:
        """
        Get configuration for a specific theme.
        
        Args:
            theme_name: Name of the theme
            
        Returns:
            ThemeConfig or None if not found
        """
        settings = self.get()
        return settings.themes.get(theme_name)

    def get_i18n_string(self, key: str, language: Optional[Language] = None) -> str:
        """
        Get internationalized string.
        
        Args:
            key: Translation key (e.g., "ui.convert_button")
            language: Language to use (defaults to current UI language)
            
        Returns:
            Translated string or key if not found
        """
        settings = self.get()
        if language is None:
            language = settings.ui.language

        i18n_data = settings.i18n.get(language.value, {})
        keys = key.split(".")
        value = i18n_data
        for k in keys:
            if isinstance(value, dict):
                value = value.get(k)
            else:
                return key

        return value if isinstance(value, str) else key

