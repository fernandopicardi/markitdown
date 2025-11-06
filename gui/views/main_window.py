"""
Main window view for MarkItDown GUI.

This module contains the main user interface window.
"""

import tkinter as tk
from tkinter import ttk, filedialog, messagebox, scrolledtext
from pathlib import Path
from typing import Optional, Callable
import logging

from gui.core.observer import Observer
from gui.core.events import Event, EventType, EventBus
from gui.core.state import AppState, ConversionState, ConversionStatus

logger = logging.getLogger(__name__)


class MainWindow(Observer, tk.Tk):
    """
    Main application window.
    
    This class implements the view layer of the MVC pattern,
    responsible for displaying the UI and handling user input.
    """

    def __init__(
        self,
        event_bus: EventBus,
        state_update_callback: Optional[Callable[[AppState], None]] = None
    ) -> None:
        """
        Initialize the main window.
        
        Args:
            event_bus: Event bus for communication
            state_update_callback: Optional callback for state updates
        """
        super().__init__()
        self.event_bus = event_bus
        self.state_update_callback = state_update_callback
        self._current_state: Optional[AppState] = None

        self._setup_window()
        self._create_widgets()
        self._setup_event_listeners()

        logger.info("Main window initialized")

    def _setup_window(self) -> None:
        """Configure the main window properties."""
        self.title("MarkItDown - File to Markdown Converter")
        self.geometry("800x600")
        self.minsize(600, 400)

        # Configure style
        style = ttk.Style()
        style.theme_use("clam")

    def _create_widgets(self) -> None:
        """Create and layout all UI widgets."""
        # Main container
        main_frame = ttk.Frame(self, padding="10")
        main_frame.grid(row=0, column=0, sticky=(tk.W, tk.E, tk.N, tk.S))
        self.columnconfigure(0, weight=1)
        self.rowconfigure(0, weight=1)

        # File selection frame
        file_frame = ttk.LabelFrame(main_frame, text="File Selection", padding="10")
        file_frame.grid(row=0, column=0, columnspan=2, sticky=(tk.W, tk.E), pady=(0, 10))
        main_frame.columnconfigure(0, weight=1)

        self.input_file_var = tk.StringVar()
        ttk.Label(file_frame, text="Input File:").grid(row=0, column=0, sticky=tk.W, padx=(0, 5))
        ttk.Entry(file_frame, textvariable=self.input_file_var, width=50, state="readonly").grid(
            row=0, column=1, sticky=(tk.W, tk.E), padx=(0, 5)
        )
        file_frame.columnconfigure(1, weight=1)
        ttk.Button(file_frame, text="Browse...", command=self._browse_input_file).grid(
            row=0, column=2, padx=(5, 0)
        )

        self.output_file_var = tk.StringVar()
        ttk.Label(file_frame, text="Output File:").grid(row=1, column=0, sticky=tk.W, padx=(0, 5), pady=(10, 0))
        ttk.Entry(file_frame, textvariable=self.output_file_var, width=50).grid(
            row=1, column=1, sticky=(tk.W, tk.E), padx=(0, 5), pady=(10, 0)
        )
        ttk.Button(file_frame, text="Browse...", command=self._browse_output_file).grid(
            row=1, column=2, padx=(5, 0), pady=(10, 0)
        )

        # Control buttons frame
        control_frame = ttk.Frame(main_frame)
        control_frame.grid(row=1, column=0, columnspan=2, sticky=(tk.W, tk.E), pady=(0, 10))
        main_frame.columnconfigure(0, weight=1)

        self.convert_button = ttk.Button(
            control_frame,
            text="Convert",
            command=self._on_convert_clicked,
            state="normal"
        )
        self.convert_button.grid(row=0, column=0, padx=(0, 5))

        self.cancel_button = ttk.Button(
            control_frame,
            text="Cancel",
            command=self._on_cancel_clicked,
            state="disabled"
        )
        self.cancel_button.grid(row=0, column=1, padx=(0, 5))

        # Progress frame
        progress_frame = ttk.LabelFrame(main_frame, text="Progress", padding="10")
        progress_frame.grid(row=2, column=0, columnspan=2, sticky=(tk.W, tk.E), pady=(0, 10))
        main_frame.columnconfigure(0, weight=1)

        self.progress_var = tk.DoubleVar()
        self.progress_bar = ttk.Progressbar(
            progress_frame,
            variable=self.progress_var,
            maximum=100,
            length=400,
            mode='determinate'
        )
        self.progress_bar.grid(row=0, column=0, sticky=(tk.W, tk.E))
        progress_frame.columnconfigure(0, weight=1)

        self.status_label = ttk.Label(progress_frame, text="Ready")
        self.status_label.grid(row=1, column=0, sticky=tk.W, pady=(5, 0))

        # Result frame
        result_frame = ttk.LabelFrame(main_frame, text="Result", padding="10")
        result_frame.grid(row=3, column=0, columnspan=2, sticky=(tk.W, tk.E, tk.N, tk.S), pady=(0, 0))
        main_frame.rowconfigure(3, weight=1)
        main_frame.columnconfigure(0, weight=1)

        self.result_text = scrolledtext.ScrolledText(
            result_frame,
            wrap=tk.WORD,
            width=80,
            height=20,
            state="disabled"
        )
        self.result_text.grid(row=0, column=0, sticky=(tk.W, tk.E, tk.N, tk.S))
        result_frame.columnconfigure(0, weight=1)
        result_frame.rowconfigure(0, weight=1)

        # Configure grid weights
        main_frame.columnconfigure(0, weight=1)
        main_frame.rowconfigure(3, weight=1)

    def _setup_event_listeners(self) -> None:
        """Set up event bus listeners."""
        self.event_bus.subscribe(EventType.CONVERSION_STARTED, self._on_conversion_started)
        self.event_bus.subscribe(EventType.CONVERSION_PROGRESS, self._on_conversion_progress)
        self.event_bus.subscribe(EventType.CONVERSION_COMPLETED, self._on_conversion_completed)
        self.event_bus.subscribe(EventType.CONVERSION_FAILED, self._on_conversion_failed)
        self.event_bus.subscribe(EventType.CONVERSION_CANCELLED, self._on_conversion_cancelled)
        self.event_bus.subscribe(EventType.UI_ERROR, self._on_ui_error)
        self.event_bus.subscribe(EventType.UI_INFO, self._on_ui_info)

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
            # Auto-suggest output file
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

        # Emit conversion request event
        self.event_bus.emit(Event(
            EventType.FILE_SELECTED,
            {
                "input_file": str(input_path),
                "output_file": str(output_path) if output_path else None
            },
            source="MainWindow"
        ))

    def _on_cancel_clicked(self) -> None:
        """Handle cancel button click."""
        self.event_bus.emit(Event(
            EventType.CONVERSION_CANCELLED,
            {},
            source="MainWindow"
        ))

    def _on_conversion_started(self, event: Event) -> None:
        """Handle conversion started event."""
        self.after(0, lambda: self._update_ui_for_conversion_start())

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
        self.convert_button.config(state="disabled")
        self.cancel_button.config(state="normal")
        self.progress_var.set(0.0)
        self.status_label.config(text="Converting...")
        self.result_text.config(state="normal")
        self.result_text.delete(1.0, tk.END)
        self.result_text.config(state="disabled")

    def _update_progress(self, progress: float) -> None:
        """Update progress bar."""
        self.progress_var.set(progress * 100)
        self.status_label.config(text=f"Converting... {int(progress * 100)}%")

    def _update_ui_for_conversion_complete(self) -> None:
        """Update UI when conversion completes."""
        self.convert_button.config(state="normal")
        self.cancel_button.config(state="disabled")
        self.progress_var.set(100.0)
        self.status_label.config(text="Conversion completed successfully!")

        # Update result text if state is available
        if self._current_state and self._current_state.current_conversion.result_text:
            self.result_text.config(state="normal")
            self.result_text.delete(1.0, tk.END)
            self.result_text.insert(1.0, self._current_state.current_conversion.result_text)
            self.result_text.config(state="disabled")

    def _update_ui_for_conversion_failed(self, error: str) -> None:
        """Update UI when conversion fails."""
        self.convert_button.config(state="normal")
        self.cancel_button.config(state="disabled")
        self.status_label.config(text=f"Conversion failed: {error}")
        messagebox.showerror("Conversion Failed", f"The conversion failed:\n{error}")

    def _update_ui_for_conversion_cancelled(self) -> None:
        """Update UI when conversion is cancelled."""
        self.convert_button.config(state="normal")
        self.cancel_button.config(state="disabled")
        self.status_label.config(text="Conversion cancelled")

    def update(self, subject: Any, event: Optional[Any] = None) -> None:
        """
        Update method from Observer pattern.
        
        Called when the observed subject (StateManager) notifies of changes.
        
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

        # Update progress
        if conversion.is_active:
            self.progress_var.set(conversion.progress * 100)
            self.status_label.config(text=f"Converting... {int(conversion.progress * 100)}%")
        elif conversion.is_complete:
            self.progress_var.set(100.0)
            self.status_label.config(text="Conversion completed")
            if conversion.result_text:
                self.result_text.config(state="normal")
                self.result_text.delete(1.0, tk.END)
                self.result_text.insert(1.0, conversion.result_text)
                self.result_text.config(state="disabled")
        elif conversion.has_error:
            self.status_label.config(text=f"Error: {conversion.error_message}")

        # Update button states
        if conversion.is_active:
            self.convert_button.config(state="disabled")
            self.cancel_button.config(state="normal")
        else:
            self.convert_button.config(state="normal")
            self.cancel_button.config(state="disabled")

    def run(self) -> None:
        """Start the main event loop."""
        logger.info("Starting main window event loop")
        self.mainloop()

