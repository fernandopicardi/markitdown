"""
Advanced workspace window with multiple tabs for MarkItDown GUI.

This module provides a sophisticated workspace system with:
- Dynamic tabs
- Multiple concurrent conversions
- State persistence
- Split view comparison
- Tab customization
"""

import customtkinter as ctk
from tkinter import filedialog, messagebox, simpledialog
from pathlib import Path
from typing import Optional, Callable, Any, Dict
import logging

from gui.core.observer import Observer
from gui.core.events import Event, EventType, EventBus
from gui.core.state import AppState, ConversionState, ConversionStatus
from gui.core.workspace import WorkspaceManager, WorkspaceState, WorkspaceStatus
from gui.components.ctk_components import (
    CTkSidebar,
    CTkStatusBar,
    CTkTopBar,
    CTkPreviewPanel,
    CTkTooltip,
    CTkAnimatedButton,
)
from gui.components.workspace_tabs import WorkspaceTabsContainer
from gui.components.split_view import SplitView

logger = logging.getLogger(__name__)


class WorkspaceView(ctk.CTkFrame):
    """View for a single workspace."""

    def __init__(
        self,
        master: Any,
        workspace: WorkspaceState,
        event_bus: EventBus,
        **kwargs
    ) -> None:
        """
        Initialize workspace view.
        
        Args:
            master: Parent widget
            workspace: Workspace state
            event_bus: Event bus
            **kwargs: Additional CTkFrame arguments
        """
        super().__init__(master, **kwargs)
        self.workspace = workspace
        self.event_bus = event_bus

        self._create_widgets()

    def _create_widgets(self) -> None:
        """Create workspace widgets."""
        # File selection frame
        file_frame = ctk.CTkFrame(self)
        file_frame.pack(fill="x", padx=20, pady=20)

        # Input file
        input_label = ctk.CTkLabel(file_frame, text="Input File:", font=ctk.CTkFont(size=14))
        input_label.grid(row=0, column=0, sticky="w", padx=10, pady=10)

        self.input_file_var = ctk.StringVar(value=self.workspace.input_file or "")
        input_entry = ctk.CTkEntry(
            file_frame,
            textvariable=self.input_file_var,
            width=400,
        )
        input_entry.grid(row=0, column=1, padx=10, pady=10, sticky="ew")
        file_frame.grid_columnconfigure(1, weight=1)

        input_browse = CTkAnimatedButton(
            file_frame,
            text="Browse...",
            command=self._browse_input_file,
            width=100,
        )
        input_browse.grid(row=0, column=2, padx=10, pady=10)

        # Output file
        output_label = ctk.CTkLabel(file_frame, text="Output File:", font=ctk.CTkFont(size=14))
        output_label.grid(row=1, column=0, sticky="w", padx=10, pady=10)

        self.output_file_var = ctk.StringVar(value=self.workspace.output_file or "")
        output_entry = ctk.CTkEntry(
            file_frame,
            textvariable=self.output_file_var,
            width=400,
        )
        output_entry.grid(row=1, column=1, padx=10, pady=10, sticky="ew")

        output_browse = CTkAnimatedButton(
            file_frame,
            text="Browse...",
            command=self._browse_output_file,
            width=100,
        )
        output_browse.grid(row=1, column=2, padx=10, pady=10)

        # Control buttons
        control_frame = ctk.CTkFrame(self)
        control_frame.pack(fill="x", padx=20, pady=20)

        self.convert_button = CTkAnimatedButton(
            control_frame,
            text="Convert",
            command=self._on_convert_clicked,
            width=150,
            height=40,
            font=ctk.CTkFont(size=14, weight="bold"),
        )
        self.convert_button.pack(side="left", padx=10, pady=10)

        self.cancel_button = CTkAnimatedButton(
            control_frame,
            text="Cancel",
            command=self._on_cancel_clicked,
            width=150,
            height=40,
            state="disabled",
        )
        self.cancel_button.pack(side="left", padx=10, pady=10)

        # Progress frame
        progress_frame = ctk.CTkFrame(self)
        progress_frame.pack(fill="x", padx=20, pady=20)

        self.progress_label = ctk.CTkLabel(
            progress_frame,
            text="Ready",
            font=ctk.CTkFont(size=12),
        )
        self.progress_label.pack(pady=10)

        self.progress_bar = ctk.CTkProgressBar(progress_frame)
        self.progress_bar.pack(fill="x", padx=20, pady=10)
        self.progress_bar.set(0)

        # Result area
        result_frame = ctk.CTkFrame(self)
        result_frame.pack(fill="both", expand=True, padx=20, pady=20)

        result_label = ctk.CTkLabel(
            result_frame,
            text="Result:",
            font=ctk.CTkFont(size=14, weight="bold"),
        )
        result_label.pack(anchor="w", padx=10, pady=5)

        self.result_text = ctk.CTkTextbox(
            result_frame,
            wrap="word",
            font=ctk.CTkFont(family="Consolas", size=11),
        )
        self.result_text.pack(fill="both", expand=True, padx=10, pady=10)

        # Load existing result
        if self.workspace.result_text:
            self.result_text.insert("1.0", self.workspace.result_text)

    def _browse_input_file(self) -> None:
        """Browse for input file."""
        file_path = filedialog.askopenfilename(
            title="Select File to Convert",
            filetypes=[
                ("All Supported", "*.pdf;*.docx;*.pptx;*.xlsx;*.html;*.csv;*.json;*.xml;*.jpg;*.png;*.mp3;*.wav"),
                ("PDF", "*.pdf"),
                ("Word", "*.docx"),
                ("PowerPoint", "*.pptx"),
                ("Excel", "*.xlsx"),
                ("All Files", "*.*")
            ]
        )
        if file_path:
            self.input_file_var.set(file_path)
            if not self.output_file_var.get():
                input_path = Path(file_path)
                output_path = input_path.with_suffix('.md')
                self.output_file_var.set(str(output_path))

    def _browse_output_file(self) -> None:
        """Browse for output file."""
        file_path = filedialog.asksaveasfilename(
            title="Save Markdown As",
            defaultextension=".md",
            filetypes=[("Markdown", "*.md"), ("Text", "*.txt"), ("All Files", "*.*")]
        )
        if file_path:
            self.output_file_var.set(file_path)

    def _on_convert_clicked(self) -> None:
        """Handle convert button click."""
        input_file = self.input_file_var.get().strip()
        if not input_file:
            messagebox.showwarning("No File Selected", "Please select an input file.")
            return

        input_path = Path(input_file)
        if not input_path.exists():
            messagebox.showerror("File Not Found", f"The file does not exist:\n{input_file}")
            return

        output_file = self.output_file_var.get().strip()
        output_path = Path(output_file) if output_file else None

        # Update workspace
        self.workspace.input_file = str(input_path)
        self.workspace.output_file = str(output_path) if output_path else None

        # Emit event with workspace ID
        self.event_bus.emit(Event(
            EventType.FILE_SELECTED,
            {
                "input_file": str(input_path),
                "output_file": str(output_path) if output_path else None,
                "workspace_id": self.workspace.workspace_id,
            },
            source="WorkspaceView"
        ))

    def _on_cancel_clicked(self) -> None:
        """Handle cancel button click."""
        self.event_bus.emit(Event(
            EventType.CONVERSION_CANCELLED,
            {"workspace_id": self.workspace.workspace_id},
            source="WorkspaceView"
        ))

    def update_workspace(self, workspace: WorkspaceState) -> None:
        """Update view with new workspace state."""
        self.workspace = workspace
        if workspace.result_text:
            self.result_text.delete("1.0", "end")
            self.result_text.insert("1.0", workspace.result_text)

        # Update progress
        if workspace.current_conversion:
            self.progress_bar.set(workspace.current_conversion.progress)
            if workspace.current_conversion.is_active:
                self.convert_button.configure(state="disabled")
                self.cancel_button.configure(state="normal")
            else:
                self.convert_button.configure(state="normal")
                self.cancel_button.configure(state="disabled")


class AdvancedWorkspaceWindow(Observer, ctk.CTk):
    """
    Advanced workspace window with multiple tabs.
    
    Features:
    - Dynamic tabs for multiple workspaces
    - Concurrent conversions
    - State persistence
    - Split view comparison
    - Tab customization
    - Keyboard shortcuts
    """

    def __init__(
        self,
        event_bus: EventBus,
        workspace_manager: Optional[WorkspaceManager] = None,
        state_update_callback: Optional[Callable[[AppState], None]] = None
    ) -> None:
        """
        Initialize advanced workspace window.
        
        Args:
            event_bus: Event bus for communication
            workspace_manager: Workspace manager (creates new if None)
            state_update_callback: Optional callback for state updates
        """
        ctk.set_appearance_mode("dark")
        ctk.set_default_color_theme("blue")

        super().__init__()
        self.event_bus = event_bus
        self.state_update_callback = state_update_callback
        self.workspace_manager = workspace_manager or WorkspaceManager()
        self._current_state: Optional[AppState] = None

        # Workspace views
        self.workspace_views: Dict[str, WorkspaceView] = {}
        self.active_workspace_id: Optional[str] = None

        # Split view
        self.split_view_enabled = False
        self.comparison_workspaces: list[str] = []
        self.split_view: Optional[SplitView] = None

        self._setup_window()
        self._create_layout()
        self._setup_event_listeners()
        self._setup_keyboard_shortcuts()

        logger.info("Advanced workspace window initialized")

    def _setup_window(self) -> None:
        """Configure window properties."""
        self.title("MarkItDown - Advanced Workspace")
        self.geometry("1600x900")
        self.minsize(1200, 700)

        self.grid_columnconfigure(1, weight=1)
        self.grid_rowconfigure(1, weight=1)

    def _create_layout(self) -> None:
        """Create main layout."""
        # Top bar
        self.top_bar = CTkTopBar(self)
        self.top_bar.grid(row=0, column=0, columnspan=3, sticky="ew", padx=0, pady=0)

        # Workspace tabs
        self.tabs_container = WorkspaceTabsContainer(
            self,
            self.workspace_manager,
            on_workspace_selected=self._on_workspace_selected,
            on_workspace_closed=self._on_workspace_closed,
            on_new_workspace=self._on_new_workspace,
        )
        self.tabs_container.grid(row=1, column=0, columnspan=3, sticky="ew", padx=5, pady=5)

        # Main workspace area (can switch between single and split view)
        self.workspace_container = ctk.CTkFrame(self)
        self.workspace_container.grid(row=2, column=0, columnspan=3, sticky="nsew", padx=5, pady=5)
        self.workspace_container.grid_columnconfigure(0, weight=1)
        self.workspace_container.grid_rowconfigure(0, weight=1)

        # Split view toggle button (in sidebar or toolbar)
        self.split_view_button = ctk.CTkButton(
            self.tabs_container,
            text="Split",
            width=60,
            height=30,
            command=self._toggle_split_view,
        )
        self.split_view_button.pack(side="right", padx=5, pady=5)

        # Status bar
        self.status_bar = CTkStatusBar(self)
        self.status_bar.grid(row=3, column=0, columnspan=3, sticky="ew", padx=0, pady=0)

        # Load initial workspace
        active_id = self.workspace_manager.active_workspace_id
        if active_id:
            self._show_workspace(active_id)
        elif self.workspace_manager.workspaces:
            first_id = list(self.workspace_manager.workspaces.keys())[0]
            self._show_workspace(first_id)

    def _setup_event_listeners(self) -> None:
        """Set up event bus listeners."""
        self.event_bus.subscribe(EventType.CONVERSION_STARTED, self._on_conversion_started)
        self.event_bus.subscribe(EventType.CONVERSION_PROGRESS, self._on_conversion_progress)
        self.event_bus.subscribe(EventType.CONVERSION_COMPLETED, self._on_conversion_completed)
        self.event_bus.subscribe(EventType.CONVERSION_FAILED, self._on_conversion_failed)

    def _setup_keyboard_shortcuts(self) -> None:
        """Set up keyboard shortcuts."""
        # Ctrl+T - New workspace
        self.bind("<Control-t>", lambda e: self._on_new_workspace())
        self.bind("<Control-T>", lambda e: self._on_new_workspace())

        # Ctrl+W - Close workspace
        self.bind("<Control-w>", lambda e: self._on_close_active_workspace())
        self.bind("<Control-W>", lambda e: self._on_close_active_workspace())

        # Ctrl+Tab - Next workspace
        self.bind("<Control-Tab>", lambda e: self._on_next_workspace())
        self.bind("<Control-ISO_Left_Tab>", lambda e: self._on_previous_workspace())

        # Ctrl+S - Save workspace
        self.bind("<Control-s>", lambda e: self._save_active_workspace())
        self.bind("<Control-S>", lambda e: self._save_active_workspace())

        # Ctrl+Shift+S - Toggle split view
        self.bind("<Control-Shift-s>", lambda e: self._toggle_split_view())
        self.bind("<Control-Shift-S>", lambda e: self._toggle_split_view())

    def _on_workspace_selected(self, workspace_id: str) -> None:
        """Handle workspace selection."""
        self._show_workspace(workspace_id)

    def _on_workspace_closed(self, workspace_id: str) -> None:
        """Handle workspace close."""
        # Confirmation
        workspace = self.workspace_manager.get_workspace(workspace_id)
        if workspace:
            if messagebox.askyesno(
                "Close Workspace",
                f"Close workspace '{workspace.name}'?\nUnsaved changes will be lost."
            ):
                self.workspace_manager.remove_workspace(workspace_id)
                self.tabs_container.remove_workspace(workspace_id)
                if workspace_id in self.workspace_views:
                    self.workspace_views[workspace_id].destroy()
                    del self.workspace_views[workspace_id]

                # Show another workspace
                if self.workspace_manager.workspaces:
                    first_id = list(self.workspace_manager.workspaces.keys())[0]
                    self._show_workspace(first_id)

    def _on_new_workspace(self) -> None:
        """Handle new workspace creation."""
        name = simpledialog.askstring(
            "New Workspace",
            "Enter workspace name:",
            initialvalue=f"Workspace {len(self.workspace_manager.workspaces) + 1}"
        )
        if name:
            workspace = self.workspace_manager.create_workspace(name=name)
            self.tabs_container.add_workspace(workspace)
            self._show_workspace(workspace.workspace_id)

    def _on_close_active_workspace(self) -> None:
        """Close active workspace."""
        if self.active_workspace_id:
            self._on_workspace_closed(self.active_workspace_id)

    def _on_next_workspace(self) -> None:
        """Switch to next workspace."""
        workspaces = self.workspace_manager.get_workspaces_in_order()
        if len(workspaces) > 1:
            current_index = next(
                (i for i, w in enumerate(workspaces) if w.workspace_id == self.active_workspace_id),
                0
            )
            next_index = (current_index + 1) % len(workspaces)
            self._show_workspace(workspaces[next_index].workspace_id)

    def _on_previous_workspace(self) -> None:
        """Switch to previous workspace."""
        workspaces = self.workspace_manager.get_workspaces_in_order()
        if len(workspaces) > 1:
            current_index = next(
                (i for i, w in enumerate(workspaces) if w.workspace_id == self.active_workspace_id),
                0
            )
            prev_index = (current_index - 1) % len(workspaces)
            self._show_workspace(workspaces[prev_index].workspace_id)

    def _show_workspace(self, workspace_id: str) -> None:
        """Show workspace view."""
        workspace = self.workspace_manager.get_workspace(workspace_id)
        if not workspace:
            return

        # Hide current workspace
        for view in self.workspace_views.values():
            view.grid_remove()

        # Show or create workspace view
        if workspace_id not in self.workspace_views:
            view = WorkspaceView(
                self.workspace_container,
                workspace,
                self.event_bus,
            )
            view.grid(row=0, column=0, sticky="nsew")
            self.workspace_views[workspace_id] = view
        else:
            self.workspace_views[workspace_id].grid(row=0, column=0, sticky="nsew")
            self.workspace_views[workspace_id].update_workspace(workspace)

        self.active_workspace_id = workspace_id
        self.tabs_container.set_active_tab(workspace_id)

    def _save_active_workspace(self) -> None:
        """Save active workspace."""
        if self.active_workspace_id:
            # Update workspace from view
            if self.active_workspace_id in self.workspace_views:
                view = self.workspace_views[self.active_workspace_id]
                workspace = self.workspace_manager.get_workspace(self.active_workspace_id)
                if workspace:
                    workspace.input_file = view.input_file_var.get()
                    workspace.output_file = view.output_file_var.get()
                    workspace.result_text = view.result_text.get("1.0", "end-1c")

            self.workspace_manager.save_workspace(self.active_workspace_id)
            self.status_bar.set_status("Workspace saved")

    def _toggle_split_view(self) -> None:
        """Toggle split view mode."""
        if self.split_view_enabled:
            # Disable split view
            if self.split_view:
                self.split_view.destroy()
                self.split_view = None
            self.split_view_enabled = False
            self.split_view_button.configure(text="Split")
            
            # Show active workspace
            if self.active_workspace_id:
                self._show_workspace(self.active_workspace_id)
        else:
            # Enable split view
            # Hide workspace views
            for view in self.workspace_views.values():
                view.grid_remove()

            # Create split view
            self.split_view = SplitView(
                self.workspace_container,
                on_close=self._toggle_split_view,
            )
            self.split_view.grid(row=0, column=0, sticky="nsew")

            # Add workspaces with results to split view
            workspaces = self.workspace_manager.get_workspaces_in_order()
            for workspace in workspaces[:3]:  # Limit to 3 for comparison
                if workspace.result_text:
                    self.split_view.add_workspace(workspace)

            self.split_view_enabled = True
            self.split_view_button.configure(text="Single")
            self.status_bar.set_status("Split view enabled - comparing workspaces")

    def _on_conversion_started(self, event: Event) -> None:
        """Handle conversion started."""
        workspace_id = event.get("workspace_id")
        if workspace_id:
            workspace = self.workspace_manager.get_workspace(workspace_id)
            if workspace:
                workspace.status = WorkspaceStatus.PROCESSING
                self.tabs_container.update_workspace_tab(workspace_id)

    def _on_conversion_progress(self, event: Event) -> None:
        """Handle conversion progress."""
        workspace_id = event.get("workspace_id")
        if workspace_id and workspace_id in self.workspace_views:
            view = self.workspace_views[workspace_id]
            progress = event.get("progress", 0.0)
            view.progress_bar.set(progress)
            view.progress_label.configure(text=f"Converting... {int(progress * 100)}%")

    def _on_conversion_completed(self, event: Event) -> None:
        """Handle conversion completed."""
        workspace_id = event.get("workspace_id")
        if workspace_id:
            workspace = self.workspace_manager.get_workspace(workspace_id)
            if workspace:
                workspace.status = WorkspaceStatus.SUCCESS
                workspace.update_status()
                # Update result text from conversion
                if workspace.current_conversion and workspace.current_conversion.result_text:
                    workspace.result_text = workspace.current_conversion.result_text
                self.workspace_manager.save_workspace(workspace_id)
                self.tabs_container.update_workspace_tab(workspace_id)
                if workspace_id in self.workspace_views:
                    self.workspace_views[workspace_id].update_workspace(workspace)
                # Update split view if enabled
                if self.split_view_enabled and self.split_view:
                    self.split_view.update_workspace(workspace)

    def _on_conversion_failed(self, event: Event) -> None:
        """Handle conversion failed."""
        workspace_id = event.get("workspace_id")
        if workspace_id:
            workspace = self.workspace_manager.get_workspace(workspace_id)
            if workspace:
                workspace.status = WorkspaceStatus.ERROR
                workspace.error_message = event.get("error", "Unknown error")
                workspace.update_status()
                self.workspace_manager.save_workspace(workspace_id)
                self.tabs_container.update_workspace_tab(workspace_id)

    def update(self, subject: Any, event: Optional[Any] = None) -> None:
        """Update from Observer pattern."""
        if isinstance(event, AppState):
            self._current_state = event

    def run(self) -> None:
        """Start the main event loop."""
        logger.info("Starting advanced workspace window")
        self.mainloop()

        # Save all workspaces on exit
        self.workspace_manager.save_all()

