"""
Views module for MarkItDown GUI.

This module contains the view components for the application.
"""

from gui.views.main_window import MainWindow
from gui.views.modern_window import ModernMainWindow
from gui.views.workspace_window import AdvancedWorkspaceWindow, WorkspaceView
from gui.views.batch_window import BatchProcessingWindow
from gui.views.template_window import TemplateManagementWindow, TemplateSelectorDialog
from gui.views.preview_window import MarkdownPreviewWindow, show_preview
from gui.views.comparison_window import DocumentComparisonWindow, show_comparison
from gui.views.plugin_window import PluginManagementWindow, show_plugin_manager
from gui.views.cloud_window import CloudStorageWindow, show_cloud_storage
from gui.views.export_window import PlatformExportWindow, show_export_window

__all__ = [
    "MainWindow",
    "ModernMainWindow",
    "AdvancedWorkspaceWindow",
    "WorkspaceView",
    "BatchProcessingWindow",
    "TemplateManagementWindow",
    "TemplateSelectorDialog",
    "MarkdownPreviewWindow",
    "show_preview",
    "DocumentComparisonWindow",
    "show_comparison",
    "PluginManagementWindow",
    "show_plugin_manager",
    "CloudStorageWindow",
    "show_cloud_storage",
    "PlatformExportWindow",
    "show_export_window",
]

