"""
Batch processing window for MarkItDown GUI.

This module provides a complete UI for batch file conversion
with filtering, preview, and real-time statistics.
"""

import customtkinter as ctk
from tkinter import filedialog, messagebox
from pathlib import Path
from typing import Optional, List, Callable, Any
import logging
import threading

from gui.core.observer import Observer
from gui.core.events import Event, EventType, EventBus
from gui.core.batch_processor import (
    BatchProcessor,
    BatchTask,
    BatchStatistics,
    FileFilter,
    TaskPriority,
)
from gui.components.batch_ui import (
    BatchPreviewPanel,
    BatchStatisticsPanel,
    BatchControlPanel,
    BatchTaskList,
)
from gui.models.conversion_model import ConversionModel

logger = logging.getLogger(__name__)


class BatchProcessingWindow(Observer, ctk.CTk):
    """
    Batch processing window with advanced features.
    
    Features:
    - File filtering
    - Preview before processing
    - Real-time statistics
    - Pause/resume/cancel
    - Task management
    """

    def __init__(
        self,
        event_bus: EventBus,
        conversion_model: ConversionModel,
        **kwargs
    ) -> None:
        """
        Initialize batch processing window.
        
        Args:
            event_bus: Event bus for communication
            conversion_model: Conversion model for processing
            **kwargs: Additional CTk arguments
        """
        super().__init__(**kwargs)
        self.event_bus = event_bus
        self.conversion_model = conversion_model

        # Batch processor
        self.batch_processor: Optional[BatchProcessor] = None
        self.update_thread: Optional[threading.Thread] = None
        self.running = False

        # File filter
        self.file_filter: Optional[FileFilter] = None
        self.selected_files: List[Path] = []

        self._setup_window()
        self._create_layout()
        self._setup_event_listeners()

        logger.info("Batch processing window initialized")

    def _setup_window(self) -> None:
        """Configure window properties."""
        self.title("MarkItDown - Batch Processing")
        self.geometry("1200x800")
        self.minsize(1000, 600)

    def _create_layout(self) -> None:
        """Create main layout."""
        # Top section - File selection and filters
        top_frame = ctk.CTkFrame(self)
        top_frame.pack(fill="x", padx=10, pady=10)

        # File selection
        file_frame = ctk.CTkFrame(top_frame)
        file_frame.pack(fill="x", padx=10, pady=10)

        ctk.CTkLabel(
            file_frame,
            text="Select Files or Directory:",
            font=ctk.CTkFont(size=14, weight="bold"),
        ).pack(side="left", padx=10)

        ctk.CTkButton(
            file_frame,
            text="Select Files",
            command=self._select_files,
            width=120,
        ).pack(side="left", padx=10)

        ctk.CTkButton(
            file_frame,
            text="Select Directory",
            command=self._select_directory,
            width=120,
        ).pack(side="left", padx=10)

        # Filters
        self._create_filters(top_frame)

        # Middle section - Preview and controls
        middle_frame = ctk.CTkFrame(self)
        middle_frame.pack(fill="both", expand=True, padx=10, pady=10)

        # Left side - Preview
        self.preview_panel = BatchPreviewPanel(
            middle_frame,
            on_start=self._start_batch,
            on_cancel=self._cancel_preview,
        )
        self.preview_panel.pack(side="left", fill="both", expand=True, padx=5)

        # Right side - Controls and statistics
        right_frame = ctk.CTkFrame(middle_frame)
        right_frame.pack(side="right", fill="y", padx=5)

        self.control_panel = BatchControlPanel(
            right_frame,
            on_pause=self._pause_batch,
            on_resume=self._resume_batch,
            on_cancel_all=self._cancel_all,
        )
        self.control_panel.pack(fill="x", padx=5, pady=5)

        self.statistics_panel = BatchStatisticsPanel(right_frame)
        self.statistics_panel.pack(fill="x", padx=5, pady=5)

        # Bottom section - Task list
        bottom_frame = ctk.CTkFrame(self)
        bottom_frame.pack(fill="both", expand=True, padx=10, pady=10)

        self.task_list = BatchTaskList(bottom_frame)
        self.task_list.pack(fill="both", expand=True)

    def _create_filters(self, parent: ctk.CTkFrame) -> None:
        """Create filter controls."""
        filter_frame = ctk.CTkFrame(parent)
        filter_frame.pack(fill="x", padx=10, pady=10)

        ctk.CTkLabel(
            filter_frame,
            text="Filters:",
            font=ctk.CTkFont(size=12, weight="bold"),
        ).pack(side="left", padx=10)

        # Extensions
        ctk.CTkLabel(filter_frame, text="Extensions:").pack(side="left", padx=5)
        self.extensions_var = ctk.StringVar(value=".pdf,.docx,.pptx,.xlsx")
        ctk.CTkEntry(
            filter_frame,
            textvariable=self.extensions_var,
            width=150,
        ).pack(side="left", padx=5)

        # Min size
        ctk.CTkLabel(filter_frame, text="Min Size (MB):").pack(side="left", padx=5)
        self.min_size_var = ctk.StringVar(value="")
        ctk.CTkEntry(
            filter_frame,
            textvariable=self.min_size_var,
            width=80,
        ).pack(side="left", padx=5)

        # Max size
        ctk.CTkLabel(filter_frame, text="Max Size (MB):").pack(side="left", padx=5)
        self.max_size_var = ctk.StringVar(value="")
        ctk.CTkEntry(
            filter_frame,
            textvariable=self.max_size_var,
            width=80,
        ).pack(side="left", padx=5)

        # Apply filters button
        ctk.CTkButton(
            filter_frame,
            text="Apply Filters",
            command=self._apply_filters,
            width=100,
        ).pack(side="left", padx=10)

    def _setup_event_listeners(self) -> None:
        """Set up event bus listeners."""
        self.event_bus.subscribe(EventType.CONVERSION_STARTED, self._on_conversion_started)
        self.event_bus.subscribe(EventType.CONVERSION_COMPLETED, self._on_conversion_completed)
        self.event_bus.subscribe(EventType.CONVERSION_FAILED, self._on_conversion_failed)

    def _select_files(self) -> None:
        """Select multiple files."""
        files = filedialog.askopenfilenames(
            title="Select Files for Batch Processing",
            filetypes=[
                ("All Supported", "*.pdf;*.docx;*.pptx;*.xlsx;*.html;*.csv;*.json;*.xml"),
                ("PDF", "*.pdf"),
                ("Word", "*.docx"),
                ("PowerPoint", "*.pptx"),
                ("Excel", "*.xlsx"),
                ("All Files", "*.*")
            ]
        )
        if files:
            self.selected_files = [Path(f) for f in files]
            self._update_preview()

    def _select_directory(self) -> None:
        """Select directory and scan for files."""
        directory = filedialog.askdirectory(title="Select Directory")
        if directory:
            dir_path = Path(directory)
            # Scan for files
            extensions = self._parse_extensions()
            files = []
            for ext in extensions:
                files.extend(dir_path.rglob(f"*{ext}"))
            self.selected_files = files
            self._apply_filters()
            self._update_preview()

    def _parse_extensions(self) -> List[str]:
        """Parse extensions from filter."""
        ext_str = self.extensions_var.get().strip()
        if not ext_str:
            return [".pdf", ".docx", ".pptx", ".xlsx"]
        return [e.strip() for e in ext_str.split(",") if e.strip()]

    def _apply_filters(self) -> None:
        """Apply file filters."""
        extensions = self._parse_extensions()
        min_size = None
        max_size = None

        try:
            min_size_str = self.min_size_var.get().strip()
            if min_size_str:
                min_size = int(float(min_size_str) * 1024 * 1024)  # MB to bytes
        except ValueError:
            pass

        try:
            max_size_str = self.max_size_var.get().strip()
            if max_size_str:
                max_size = int(float(max_size_str) * 1024 * 1024)  # MB to bytes
        except ValueError:
            pass

        self.file_filter = FileFilter(
            extensions=extensions,
            min_size=min_size,
            max_size=max_size,
        )

        if self.file_filter:
            self.selected_files = self.file_filter.filter_files(self.selected_files)
            self._update_preview()

    def _update_preview(self) -> None:
        """Update preview panel."""
        self.preview_panel.set_files(self.selected_files)

    def _start_batch(self) -> None:
        """Start batch processing."""
        if not self.selected_files:
            messagebox.showwarning("No Files", "Please select files to process.")
            return

        # Create batch processor with async support
        async def async_conversion_func(input_file: str, output_file: Optional[str] = None) -> Dict[str, Any]:
            """Async conversion function for I/O-bound operations."""
            try:
                # Run conversion in executor to avoid blocking
                loop = asyncio.get_event_loop()
                result = await loop.run_in_executor(
                    None,
                    lambda: self.conversion_model.convert(
                        Path(input_file),
                        Path(output_file) if output_file else None
                    )
                )
                return {
                    "text_content": result.result_text or "",
                }
            except Exception as e:
                raise Exception(str(e))

        def sync_conversion_func(input_file: str, output_file: Optional[str] = None) -> Dict[str, Any]:
            """Sync conversion function for CPU-bound operations."""
            try:
                result = self.conversion_model.convert(
                    Path(input_file),
                    Path(output_file) if output_file else None
                )
                return {
                    "text_content": result.result_text or "",
                }
            except Exception as e:
                raise Exception(str(e))

        # Use async for I/O-bound, sync for CPU-bound
        # For file I/O, async is better; for CPU-intensive, use processes
        use_async = True  # Use async for I/O-bound operations
        use_processes = False  # Set to True for CPU-bound operations

        self.batch_processor = BatchProcessor(
            event_bus=self.event_bus,
            max_workers=4,
            use_processes=use_processes,
            conversion_func=sync_conversion_func if not use_async else None,
            async_conversion_func=async_conversion_func if use_async else None,
        )

        # Add files to queue
        output_dir = Path.home() / "MarkItDown" / "batch_output"
        output_dir.mkdir(parents=True, exist_ok=True)

        tasks = self.batch_processor.add_files(
            file_paths=self.selected_files,
            output_dir=output_dir,
            file_filter=self.file_filter,
            priority=TaskPriority.NORMAL,
        )

        # Add tasks to UI
        for task in tasks:
            self.task_list.add_task(task)

        # Start processing
        self.batch_processor.start()
        self.running = True

        # Start update thread
        self.update_thread = threading.Thread(target=self._update_loop, daemon=True)
        self.update_thread.start()

        logger.info(f"Batch processing started with {len(tasks)} tasks")

    def _cancel_preview(self) -> None:
        """Cancel preview and clear selection."""
        self.selected_files = []
        self._update_preview()

    def _pause_batch(self) -> None:
        """Pause batch processing."""
        if self.batch_processor:
            self.batch_processor.pause()

    def _resume_batch(self) -> None:
        """Resume batch processing."""
        if self.batch_processor:
            self.batch_processor.resume()

    def _cancel_all(self) -> None:
        """Cancel all batch processing."""
        if messagebox.askyesno("Cancel All", "Cancel all batch processing?"):
            if self.batch_processor:
                self.batch_processor.cancel_all()
            self.running = False

    def _update_loop(self) -> None:
        """Update loop for statistics."""
        while self.running:
            try:
                if self.batch_processor:
                    stats = self.batch_processor.get_statistics()
                    self.after(0, lambda s=stats: self.statistics_panel.update_statistics(s))

                    # Update task list
                    tasks = self.batch_processor.get_all_tasks()
                    for task in tasks:
                        self.after(0, lambda t=task: self.task_list.update_task(t))

                    # Check if done
                    if stats.completed_tasks + stats.failed_tasks + stats.cancelled_tasks >= stats.total_tasks:
                        if stats.total_tasks > 0:
                            self.running = False
                            self.after(0, self._on_batch_complete)

                threading.Event().wait(1.0)  # Update every second
            except Exception as e:
                logger.error(f"Error in update loop: {e}")

    def _on_batch_complete(self) -> None:
        """Handle batch completion."""
        if self.batch_processor:
            stats = self.batch_processor.get_statistics()
            messagebox.showinfo(
                "Batch Complete",
                f"Batch processing completed!\n\n"
                f"Total: {stats.total_tasks}\n"
                f"Completed: {stats.completed_tasks}\n"
                f"Failed: {stats.failed_tasks}\n"
                f"Success Rate: {stats.success_rate:.1f}%"
            )

    def _on_conversion_started(self, event: Event) -> None:
        """Handle conversion started event."""
        task_id = event.get("task_id")
        if task_id and self.batch_processor:
            task = self.batch_processor.get_task(task_id)
            if task:
                self.after(0, lambda t=task: self.task_list.update_task(t))

    def _on_conversion_completed(self, event: Event) -> None:
        """Handle conversion completed event."""
        task_id = event.get("task_id")
        if task_id and self.batch_processor:
            task = self.batch_processor.get_task(task_id)
            if task:
                self.after(0, lambda t=task: self.task_list.update_task(t))

    def _on_conversion_failed(self, event: Event) -> None:
        """Handle conversion failed event."""
        task_id = event.get("task_id")
        if task_id and self.batch_processor:
            task = self.batch_processor.get_task(task_id)
            if task:
                self.after(0, lambda t=task: self.task_list.update_task(t))

    def update(self, subject: Any, event: Optional[Any] = None) -> None:
        """Update from Observer pattern."""
        pass

    def run(self) -> None:
        """Start the window."""
        logger.info("Starting batch processing window")
        self.mainloop()

        # Cleanup on close
        if self.batch_processor:
            self.batch_processor.stop()
        self.running = False

