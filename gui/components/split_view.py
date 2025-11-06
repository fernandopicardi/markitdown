"""
Split view component for comparing multiple workspaces side by side.
"""

import customtkinter as ctk
from typing import List, Optional, Callable, Any
import logging

from gui.core.workspace import WorkspaceState

logger = logging.getLogger(__name__)


class SplitViewPanel(ctk.CTkFrame):
    """Panel in split view showing a workspace."""

    def __init__(
        self,
        master: Any,
        workspace: WorkspaceState,
        **kwargs
    ) -> None:
        """
        Initialize split view panel.
        
        Args:
            master: Parent widget
            workspace: Workspace to display
            **kwargs: Additional CTkFrame arguments
        """
        super().__init__(master, **kwargs)
        self.workspace = workspace

        # Header
        header = ctk.CTkFrame(self)
        header.pack(fill="x", padx=5, pady=5)

        name_label = ctk.CTkLabel(
            header,
            text=workspace.name,
            font=ctk.CTkFont(size=14, weight="bold"),
        )
        name_label.pack(side="left", padx=10)

        # Content
        self.content_text = ctk.CTkTextbox(
            self,
            wrap="word",
            font=ctk.CTkFont(family="Consolas", size=10),
        )
        self.content_text.pack(fill="both", expand=True, padx=5, pady=5)

        # Load content
        if workspace.result_text:
            self.content_text.insert("1.0", workspace.result_text)

    def update_workspace(self, workspace: WorkspaceState) -> None:
        """Update panel with new workspace."""
        self.workspace = workspace
        self.content_text.delete("1.0", "end")
        if workspace.result_text:
            self.content_text.insert("1.0", workspace.result_text)


class SplitView(ctk.CTkFrame):
    """Split view for comparing multiple workspaces."""

    def __init__(
        self,
        master: Any,
        on_close: Optional[Callable[[], None]] = None,
        **kwargs
    ) -> None:
        """
        Initialize split view.
        
        Args:
            master: Parent widget
            on_close: Callback when split view is closed
            **kwargs: Additional CTkFrame arguments
        """
        super().__init__(master, **kwargs)
        self.on_close = on_close
        self.panels: List[SplitViewPanel] = []

        # Header
        header = ctk.CTkFrame(self)
        header.pack(fill="x", padx=5, pady=5)

        title_label = ctk.CTkLabel(
            header,
            text="Split View Comparison",
            font=ctk.CTkFont(size=16, weight="bold"),
        )
        title_label.pack(side="left", padx=10)

        close_button = ctk.CTkButton(
            header,
            text="Close",
            command=self._on_close_clicked,
            width=80,
        )
        close_button.pack(side="right", padx=10)

        # Container for panels
        self.panels_container = ctk.CTkFrame(self)
        self.panels_container.pack(fill="both", expand=True, padx=5, pady=5)

    def add_workspace(self, workspace: WorkspaceState) -> None:
        """
        Add workspace to split view.
        
        Args:
            workspace: Workspace to add
        """
        panel = SplitViewPanel(
            self.panels_container,
            workspace,
        )
        panel.pack(side="left", fill="both", expand=True, padx=5, pady=5)
        self.panels.append(panel)

        # Update layout
        self._update_layout()

    def remove_workspace(self, workspace_id: str) -> None:
        """
        Remove workspace from split view.
        
        Args:
            workspace_id: Workspace ID to remove
        """
        panel_to_remove = None
        for panel in self.panels:
            if panel.workspace.workspace_id == workspace_id:
                panel_to_remove = panel
                break

        if panel_to_remove:
            panel_to_remove.destroy()
            self.panels.remove(panel_to_remove)
            self._update_layout()

    def update_workspace(self, workspace: WorkspaceState) -> None:
        """
        Update workspace in split view.
        
        Args:
            workspace: Updated workspace
        """
        for panel in self.panels:
            if panel.workspace.workspace_id == workspace.workspace_id:
                panel.update_workspace(workspace)
                break

    def _update_layout(self) -> None:
        """Update split view layout."""
        # Configure columns based on number of panels
        num_panels = len(self.panels)
        if num_panels > 0:
            for i in range(num_panels):
                self.panels_container.grid_columnconfigure(i, weight=1)

    def _on_close_clicked(self) -> None:
        """Handle close button click."""
        if self.on_close:
            self.on_close()

    def clear(self) -> None:
        """Clear all panels."""
        for panel in self.panels:
            panel.destroy()
        self.panels.clear()

