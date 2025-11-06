"""
Modern Main Window using CustomTkinter for MarkItDown GUI.

This module provides a modern, responsive UI with CustomTkinter.
"""

import customtkinter as ctk
from tkinter import filedialog, messagebox
from pathlib import Path
from typing import Optional, Callable, Any
import logging
import threading

from gui.core.observer import Observer
from gui.core.events import Event, EventType, EventBus
from gui.core.state import AppState, ConversionState, ConversionStatus
from gui.components.ctk_components import (
    CTkSidebar,
    CTkStatusBar,
    CTkTopBar,
    CTkPreviewPanel,
    CTkTooltip,
    CTkIconButton,
    CTkAnimatedButton,
)

logger = logging.getLogger(__name__)


class ModernMainWindow(Observer, ctk.CTk):
    """
    Modern main window using CustomTkinter.
    
    Features:
    - Retractable sidebar
    - Tabbed workspace
    - Preview panel
    - Status bar
    - Top bar with profile
    - Theme switching
    - Drag & Drop
    - Keyboard shortcuts
    - Animations
    - Accessibility
    """

    def __init__(
        self,
        event_bus: EventBus,
        state_update_callback: Optional[Callable[[AppState], None]] = None
    ) -> None:
        """
        Initialize the modern main window.
        
        Args:
            event_bus: Event bus for communication
            state_update_callback: Optional callback for state updates
        """
        # Set appearance mode and color theme
        ctk.set_appearance_mode("dark")
        ctk.set_default_color_theme("blue")

        super().__init__()
        self.event_bus = event_bus
        self.state_update_callback = state_update_callback
        self._current_state: Optional[AppState] = None
        self._current_theme = "dark"

        self._setup_window()
        self._create_layout()
        self._setup_event_listeners()
        self._setup_keyboard_shortcuts()
        self._setup_drag_drop()
        self._setup_accessibility()

        logger.info("Modern main window initialized")

    def _setup_window(self) -> None:
        """Configure the main window properties."""
        self.title("MarkItDown - File to Markdown Converter")
        self.geometry("1400x800")
        self.minsize(1000, 600)

        # Configure grid weights for responsiveness
        self.grid_columnconfigure(1, weight=1)
        self.grid_rowconfigure(1, weight=1)

    def _create_layout(self) -> None:
        """Create the main layout."""
        # Top bar
        self.top_bar = CTkTopBar(self)
        self.top_bar.grid(row=0, column=0, columnspan=3, sticky="ew", padx=0, pady=0)
        self.top_bar.set_theme_callback(self._toggle_theme)
        self.top_bar.set_settings_callback(self._open_settings)
        self.top_bar.set_profile_callback(self._open_profile)

        # Sidebar
        self.sidebar = CTkSidebar(self, width=250, collapsed_width=60)
        self.sidebar.grid(row=1, column=0, sticky="nsew", padx=5, pady=5)

        # Add menu items
        self.sidebar.add_menu_item(
            "Convert",
            command=self._on_convert_clicked,
            icon_path=None,
        )
        self.sidebar.add_menu_item(
            "History",
            command=self._on_history_clicked,
            icon_path=None,
        )
        self.sidebar.add_menu_item(
            "Settings",
            command=self._open_settings,
            icon_path=None,
        )

        # Main workspace (center)
        self.workspace = ctk.CTkTabview(self)
        self.workspace.grid(row=1, column=1, sticky="nsew", padx=5, pady=5)

        # Create tabs
        self.convert_tab = self.workspace.add("Convert")
        self.history_tab = self.workspace.add("History")
        self.settings_tab = self.workspace.add("Settings")

        self._create_convert_tab()
        self._create_history_tab()
        self._create_settings_tab()

        # Preview panel (right)
        self.preview_panel = CTkPreviewPanel(self, width=400)
        self.preview_panel.grid(row=1, column=2, sticky="nsew", padx=5, pady=5)

        # Status bar
        self.status_bar = CTkStatusBar(self)
        self.status_bar.grid(row=2, column=0, columnspan=3, sticky="ew", padx=0, pady=0)

        # Configure column weights for responsiveness
        self.grid_columnconfigure(1, weight=1)  # Workspace expands
        self.grid_columnconfigure(2, weight=0, minsize=400)  # Preview panel

    def _create_convert_tab(self) -> None:
        """Create the convert tab."""
        # File selection frame
        file_frame = ctk.CTkFrame(self.convert_tab)
        file_frame.pack(fill="x", padx=20, pady=20)

        # Input file
        input_label = ctk.CTkLabel(file_frame, text="Input File:", font=ctk.CTkFont(size=14))
        input_label.grid(row=0, column=0, sticky="w", padx=10, pady=10)

        self.input_file_var = ctk.StringVar(value="")
        input_entry = ctk.CTkEntry(
            file_frame,
            textvariable=self.input_file_var,
            width=400,
            state="readonly",
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
        CTkTooltip(input_browse, "Select file to convert (Ctrl+O)")

        # Output file
        output_label = ctk.CTkLabel(file_frame, text="Output File:", font=ctk.CTkFont(size=14))
        output_label.grid(row=1, column=0, sticky="w", padx=10, pady=10)

        self.output_file_var = ctk.StringVar(value="")
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
        CTkTooltip(output_browse, "Select output location (optional)")

        # Control buttons
        control_frame = ctk.CTkFrame(self.convert_tab)
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
        CTkTooltip(self.convert_button, "Start conversion (Ctrl+Enter)")

        self.cancel_button = CTkAnimatedButton(
            control_frame,
            text="Cancel",
            command=self._on_cancel_clicked,
            width=150,
            height=40,
            state="disabled",
        )
        self.cancel_button.pack(side="left", padx=10, pady=10)
        CTkTooltip(self.cancel_button, "Cancel conversion (Esc)")

        # Progress frame
        progress_frame = ctk.CTkFrame(self.convert_tab)
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
        result_frame = ctk.CTkFrame(self.convert_tab)
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

    def _create_history_tab(self) -> None:
        """Create the history tab."""
        history_label = ctk.CTkLabel(
            self.history_tab,
            text="Conversion History",
            font=ctk.CTkFont(size=16, weight="bold"),
        )
        history_label.pack(pady=20)

        # History list (placeholder)
        self.history_list = ctk.CTkTextbox(self.history_tab)
        self.history_list.pack(fill="both", expand=True, padx=20, pady=20)
        self.history_list.insert("1.0", "No conversion history yet.")

    def _create_settings_tab(self) -> None:
        """Create the settings tab."""
        settings_label = ctk.CTkLabel(
            self.settings_tab,
            text="Settings",
            font=ctk.CTkFont(size=16, weight="bold"),
        )
        settings_label.pack(pady=20)

        # Settings content (placeholder)
        settings_text = ctk.CTkTextbox(self.settings_tab)
        settings_text.pack(fill="both", expand=True, padx=20, pady=20)
        settings_text.insert("1.0", "Settings panel - to be implemented")

    def _setup_event_listeners(self) -> None:
        """Set up event bus listeners."""
        self.event_bus.subscribe(EventType.CONVERSION_STARTED, self._on_conversion_started)
        self.event_bus.subscribe(EventType.CONVERSION_PROGRESS, self._on_conversion_progress)
        self.event_bus.subscribe(EventType.CONVERSION_COMPLETED, self._on_conversion_completed)
        self.event_bus.subscribe(EventType.CONVERSION_FAILED, self._on_conversion_failed)
        self.event_bus.subscribe(EventType.CONVERSION_CANCELLED, self._on_conversion_cancelled)
        self.event_bus.subscribe(EventType.UI_ERROR, self._on_ui_error)
        self.event_bus.subscribe(EventType.UI_INFO, self._on_ui_info)

    def _setup_keyboard_shortcuts(self) -> None:
        """Set up keyboard shortcuts."""
        # Ctrl+O - Open file
        self.bind("<Control-o>", lambda e: self._browse_input_file())
        self.bind("<Control-O>", lambda e: self._browse_input_file())

        # Ctrl+S - Save
        self.bind("<Control-s>", lambda e: self._save_result())
        self.bind("<Control-S>", lambda e: self._save_result())

        # Ctrl+Enter - Convert
        self.bind("<Control-Return>", lambda e: self._on_convert_clicked())

        # Esc - Cancel
        self.bind("<Escape>", lambda e: self._on_cancel_clicked())

        # F5 - Refresh
        self.bind("<F5>", lambda e: self._refresh())

        # Tab navigation
        self.bind("<Tab>", self._on_tab)

    def _setup_drag_drop(self) -> None:
        """Set up drag and drop functionality."""
        try:
            from tkinterdnd2 import DND_FILES, TkinterDnD
            # CustomTkinter wraps tkinter, access via .tk attribute
            # Register drop target on the underlying tkinter window
            if hasattr(self, 'tk'):
                self.tk.drop_target_register(DND_FILES)
                self.tk.dnd_bind('<<Drop>>', self._on_file_drop)
                logger.info("Drag & Drop enabled on main window")
            
            # Also enable on convert tab area
            # Note: CTkTabview may need special handling
            try:
                if hasattr(self.convert_tab, 'tk'):
                    self.convert_tab.tk.drop_target_register(DND_FILES)
                    self.convert_tab.tk.dnd_bind('<<Drop>>', self._on_file_drop)
                    logger.info("Drag & Drop enabled on convert tab")
            except Exception as e:
                logger.debug(f"Could not enable DnD on tab: {e}")
        except ImportError:
            logger.warning("tkinterdnd2 not available, drag & drop disabled")
        except Exception as e:
            logger.warning(f"Failed to enable drag & drop: {e}")

    def _setup_accessibility(self) -> None:
        """Set up accessibility features."""
        # Focus traversal
        self.bind("<Tab>", self._on_tab)
        self.bind("<Shift-Tab>", self._on_shift_tab)

        # Screen reader support (if available)
        # Can be extended with accessibility libraries

    def _on_tab(self, event: Any) -> None:
        """Handle Tab key for navigation."""
        # Focus next widget
        event.widget.tk_focusNext().focus()
        return "break"

    def _on_shift_tab(self, event: Any) -> None:
        """Handle Shift+Tab for reverse navigation."""
        event.widget.tk_focusPrev().focus()
        return "break"

    def _on_file_drop(self, event: Any) -> None:
        """Handle file drop event."""
        try:
            # Handle both tkinterdnd2 and standard drop events
            if hasattr(event, 'data'):
                files = self.tk.splitlist(event.data) if hasattr(self.tk, 'splitlist') else [event.data]
            else:
                files = [str(event)]
            
            if files:
                file_path = files[0].strip('{}').strip('"').strip("'")
                if Path(file_path).exists():
                    self.input_file_var.set(file_path)
                    # Auto-suggest output
                    if not self.output_file_var.get():
                        input_path = Path(file_path)
                        output_path = input_path.with_suffix('.md')
                        self.output_file_var.set(str(output_path))
                    self.status_bar.set_status(f"File dropped: {Path(file_path).name}")
                    # Switch to convert tab
                    self.workspace.set("Convert")
        except Exception as e:
            logger.error(f"Error handling file drop: {e}")
            self.status_bar.set_status(f"Error: Could not load dropped file")

    def _browse_input_file(self) -> None:
        """Open file dialog to select input file."""
        file_path = filedialog.askopenfilename(
            title="Select File to Convert",
            filetypes=[
                ("All Supported", "*.pdf;*.docx;*.pptx;*.xlsx;*.html;*.csv;*.json;*.xml;*.jpg;*.png;*.mp3;*.wav"),
                ("PDF", "*.pdf"),
                ("Word", "*.docx"),
                ("PowerPoint", "*.pptx"),
                ("Excel", "*.xlsx"),
                ("HTML", "*.html"),
                ("Images", "*.jpg;*.png;*.jpeg;*.gif"),
                ("Audio", "*.mp3;*.wav;*.m4a"),
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
        """Open file dialog to select output file."""
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

        self.event_bus.emit(Event(
            EventType.FILE_SELECTED,
            {
                "input_file": str(input_path),
                "output_file": str(output_path) if output_path else None
            },
            source="ModernMainWindow"
        ))

    def _on_cancel_clicked(self) -> None:
        """Handle cancel button click."""
        self.event_bus.emit(Event(
            EventType.CONVERSION_CANCELLED,
            {},
            source="ModernMainWindow"
        ))

    def _save_result(self) -> None:
        """Save result to file."""
        content = self.result_text.get("1.0", "end-1c")
        if not content.strip():
            messagebox.showwarning("No Content", "No content to save.")
            return

        file_path = filedialog.asksaveasfilename(
            title="Save Result",
            defaultextension=".md",
            filetypes=[("Markdown", "*.md"), ("Text", "*.txt"), ("All Files", "*.*")]
        )
        if file_path:
            try:
                Path(file_path).write_text(content, encoding='utf-8')
                self.status_bar.set_status(f"Saved to: {Path(file_path).name}")
            except Exception as e:
                messagebox.showerror("Save Error", f"Failed to save file:\n{e}")

    def _refresh(self) -> None:
        """Refresh the interface."""
        self.status_bar.set_status("Refreshed")

    def _on_history_clicked(self) -> None:
        """Handle history menu click."""
        self.workspace.set("History")

    def _toggle_theme(self) -> None:
        """Toggle between dark and light theme."""
        current_mode = ctk.get_appearance_mode()
        new_mode = "light" if current_mode == "Dark" else "dark"
        ctk.set_appearance_mode(new_mode)
        self._current_theme = new_mode
        self.status_bar.set_status(f"Theme switched to {new_mode}")

    def _open_settings(self) -> None:
        """Open settings dialog."""
        self.workspace.set("Settings")
        self.status_bar.set_status("Settings opened")

    def _open_profile(self) -> None:
        """Open profile dialog."""
        messagebox.showinfo("Profile", "Profile settings - to be implemented")

    def _on_conversion_started(self, event: Event) -> None:
        """Handle conversion started event."""
        self.after(0, self._update_ui_for_conversion_start)

    def _on_conversion_progress(self, event: Event) -> None:
        """Handle conversion progress event."""
        progress = event.get("progress", 0.0)
        self.after(0, lambda p=progress: self._update_progress(p))

    def _on_conversion_completed(self, event: Event) -> None:
        """Handle conversion completed event."""
        self.after(0, self._update_ui_for_conversion_complete)

    def _on_conversion_failed(self, event: Event) -> None:
        """Handle conversion failed event."""
        error = event.get("error", "Unknown error")
        self.after(0, lambda e=error: self._update_ui_for_conversion_failed(e))

    def _on_conversion_cancelled(self, event: Event) -> None:
        """Handle conversion cancelled event."""
        self.after(0, self._update_ui_for_conversion_cancelled)

    def _on_ui_error(self, event: Event) -> None:
        """Handle UI error event."""
        message = event.get("message", "An error occurred")
        self.after(0, lambda m=message: messagebox.showerror("Error", m))

    def _on_ui_info(self, event: Event) -> None:
        """Handle UI info event."""
        message = event.get("message", "")
        self.after(0, lambda m=message: messagebox.showinfo("Information", m))

    def _update_ui_for_conversion_start(self) -> None:
        """Update UI when conversion starts."""
        self.convert_button.configure(state="disabled")
        self.cancel_button.configure(state="normal")
        self.progress_bar.set(0.0)
        self.progress_label.configure(text="Converting...")
        self.status_bar.set_status("Conversion started")
        self.result_text.delete("1.0", "end")

    def _update_progress(self, progress: float) -> None:
        """Update progress bar."""
        self.progress_bar.set(progress)
        self.progress_label.configure(text=f"Converting... {int(progress * 100)}%")
        self.status_bar.set_progress(f"{int(progress * 100)}%")

    def _update_ui_for_conversion_complete(self) -> None:
        """Update UI when conversion completes."""
        self.convert_button.configure(state="normal")
        self.cancel_button.configure(state="disabled")
        self.progress_bar.set(1.0)
        self.progress_label.configure(text="Conversion completed!")
        self.status_bar.set_status("Conversion completed successfully")

        if self._current_state and self._current_state.current_conversion.result_text:
            result = self._current_state.current_conversion.result_text
            self.result_text.delete("1.0", "end")
            self.result_text.insert("1.0", result)
            self.preview_panel.set_content(result)

    def _update_ui_for_conversion_failed(self, error: str) -> None:
        """Update UI when conversion fails."""
        self.convert_button.configure(state="normal")
        self.cancel_button.configure(state="disabled")
        self.progress_label.configure(text=f"Conversion failed: {error}")
        self.status_bar.set_status(f"Conversion failed: {error}")
        messagebox.showerror("Conversion Failed", f"The conversion failed:\n{error}")

    def _update_ui_for_conversion_cancelled(self) -> None:
        """Update UI when conversion is cancelled."""
        self.convert_button.configure(state="normal")
        self.cancel_button.configure(state="disabled")
        self.progress_label.configure(text="Conversion cancelled")
        self.status_bar.set_status("Conversion cancelled")

    def update(self, subject: Any, event: Optional[Any] = None) -> None:
        """
        Update method from Observer pattern.
        
        Args:
            subject: The observable subject
            event: Optional event data
        """
        if isinstance(event, AppState):
            self._current_state = event
            self._update_ui_from_state(event)

    def _update_ui_from_state(self, state: AppState) -> None:
        """
        Update UI elements from application state.
        
        Args:
            state: Current application state
        """
        conversion = state.current_conversion

        if conversion.is_active:
            self.progress_bar.set(conversion.progress)
            self.progress_label.configure(text=f"Converting... {int(conversion.progress * 100)}%")
        elif conversion.is_complete:
            self.progress_bar.set(1.0)
            if conversion.result_text:
                self.result_text.delete("1.0", "end")
                self.result_text.insert("1.0", conversion.result_text)
                self.preview_panel.set_content(conversion.result_text)

        if conversion.is_active:
            self.convert_button.configure(state="disabled")
            self.cancel_button.configure(state="normal")
        else:
            self.convert_button.configure(state="normal")
            self.cancel_button.configure(state="disabled")

    def run(self) -> None:
        """Start the main event loop."""
        logger.info("Starting modern main window event loop")
        self.mainloop()

