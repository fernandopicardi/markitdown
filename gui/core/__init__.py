"""
Core module for MarkItDown GUI.

This module contains the core architecture components including:
- Observer pattern implementation
- Event system
- State management
- Application base class
"""

from gui.core.observer import Observer, Observable
from gui.core.events import Event, EventType, EventBus
from gui.core.state import AppState, StateManager, ConversionState, ConversionStatus
from gui.core.workspace import (
    WorkspaceManager,
    WorkspaceState,
    WorkspaceStatus,
)
from gui.core.batch_processor import (
    BatchProcessor,
    BatchTask,
    BatchStatistics,
    FileFilter,
    TaskPriority,
    TaskStatus,
)
from gui.core.templates import (
    TemplateManager,
    MarkdownTemplate,
    PostProcessingRule,
    PostProcessingPipeline,
    TemplateCategory,
)
from gui.core.markdown_renderer import (
    MarkdownRenderer,
    RenderOptions,
    PreviewTheme,
)
from gui.core.document_comparator import (
    DocumentComparator,
    DiffSegment,
    DiffType,
    ConversionStatistics,
)
from gui.core.plugin_system import (
    PluginManager,
    AbstractPlugin,
    PluginMetadata,
    PluginType,
    PluginStatus,
)
from gui.core.cloud_storage import (
    CloudStorageManager,
    CloudStorageProvider,
    CloudProvider,
    CloudFile,
    SyncStatus,
    SyncTask,
)
from gui.core.exporters import (
    ExportManager,
    AbstractExporter,
    ExportPlatform,
    ExportMapping,
    ExportResult,
    ExportStatus,
    ExportHistory,
)

__all__ = [
    "Observer",
    "Observable",
    "Event",
    "EventType",
    "EventBus",
    "AppState",
    "StateManager",
    "ConversionState",
    "ConversionStatus",
    "WorkspaceManager",
    "WorkspaceState",
    "WorkspaceStatus",
    "BatchProcessor",
    "BatchTask",
    "BatchStatistics",
    "FileFilter",
    "TaskPriority",
    "TaskStatus",
    "TemplateManager",
    "MarkdownTemplate",
    "PostProcessingRule",
    "PostProcessingPipeline",
    "TemplateCategory",
    "MarkdownRenderer",
    "RenderOptions",
    "PreviewTheme",
    "DocumentComparator",
    "DiffSegment",
    "DiffType",
    "ConversionStatistics",
    "PluginManager",
    "AbstractPlugin",
    "PluginMetadata",
    "PluginType",
    "PluginStatus",
    "CloudStorageManager",
    "CloudStorageProvider",
    "CloudProvider",
    "CloudFile",
    "SyncStatus",
    "SyncTask",
    "ExportManager",
    "AbstractExporter",
    "ExportPlatform",
    "ExportMapping",
    "ExportResult",
    "ExportStatus",
    "ExportHistory",
]

