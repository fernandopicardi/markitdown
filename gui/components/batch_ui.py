"""
Batch processing UI components for MarkItDown GUI.
"""

import customtkinter as ctk
from pathlib import Path
from typing import List, Optional, Callable, Dict
import logging

from gui.core.batch_processor import (
    BatchProcessor,
    BatchTask,
    BatchStatistics,
    FileFilter,
    TaskPriority,
    TaskStatus,
)

logger = logging.getLogger(__name__)


class BatchPreviewPanel(ctk.CTkFrame):
    """Preview panel for batch file list."""

    def __init__(
        self,
        master: Any,
        on_start: Optional[Callable[[], None]] = None,
        on_cancel: Optional[Callable[[], None]] = None,
        **kwargs
    ) -> None:
        """
        Initialize preview panel.
        
        Args:
            master: Parent widget
            on_start: Callback when start is clicked
            on_cancel: Callback when cancel is clicked
            **kwargs: Additional CTkFrame arguments
        """
        super().__init__(master, **kwargs)
        self.on_start = on_start
        self.on_cancel = on_cancel
        self.file_list: List[Path] = []

        self._create_widgets()

    def _create_widgets(self) -> None:
        """Create preview widgets."""
        # Header
        header = ctk.CTkFrame(self)
        header.pack(fill="x", padx=10, pady=10)

        title = ctk.CTkLabel(
            header,
            text="Batch Conversion Preview",
            font=ctk.CTkFont(size=16, weight="bold"),
        )
        title.pack(side="left", padx=10)

        self.count_label = ctk.CTkLabel(
            header,
            text="0 files",
            font=ctk.CTkFont(size=12),
        )
        self.count_label.pack(side="right", padx=10)

        # File list
        self.file_listbox = ctk.CTkTextbox(
            self,
            wrap="none",
            font=ctk.CTkFont(family="Consolas", size=10),
        )
        self.file_listbox.pack(fill="both", expand=True, padx=10, pady=10)

        # Buttons
        button_frame = ctk.CTkFrame(self)
        button_frame.pack(fill="x", padx=10, pady=10)

        self.start_button = ctk.CTkButton(
            button_frame,
            text="Start Batch",
            command=self._on_start_clicked,
            width=120,
            height=35,
            font=ctk.CTkFont(size=14, weight="bold"),
        )
        self.start_button.pack(side="left", padx=10)

        self.cancel_button = ctk.CTkButton(
            button_frame,
            text="Cancel",
            command=self._on_cancel_clicked,
            width=120,
            height=35,
        )
        self.cancel_button.pack(side="left", padx=10)

    def set_files(self, file_list: List[Path]) -> None:
        """
        Set file list to preview.
        
        Args:
            file_list: List of file paths
        """
        self.file_list = file_list
        self.file_listbox.delete("1.0", "end")

        for i, file_path in enumerate(file_list, 1):
            self.file_listbox.insert("end", f"{i}. {file_path}\n")

        self.count_label.configure(text=f"{len(file_list)} files")

    def _on_start_clicked(self) -> None:
        """Handle start button click."""
        if self.on_start:
            self.on_start()

    def _on_cancel_clicked(self) -> None:
        """Handle cancel button click."""
        if self.on_cancel:
            self.on_cancel()


class BatchStatisticsPanel(ctk.CTkFrame):
    """Real-time statistics panel for batch processing."""

    def __init__(self, master: Any, **kwargs) -> None:
        """Initialize statistics panel."""
        super().__init__(master, **kwargs)
        self._create_widgets()

    def _create_widgets(self) -> None:
        """Create statistics widgets."""
        title = ctk.CTkLabel(
            self,
            text="Batch Statistics",
            font=ctk.CTkFont(size=14, weight="bold"),
        )
        title.pack(pady=10)

        # Statistics grid
        self.stats_frame = ctk.CTkFrame(self)
        self.stats_frame.pack(fill="both", expand=True, padx=10, pady=10)

        # Labels
        self.total_label = ctk.CTkLabel(self.stats_frame, text="Total: 0")
        self.total_label.grid(row=0, column=0, sticky="w", padx=10, pady=5)

        self.completed_label = ctk.CTkLabel(self.stats_frame, text="Completed: 0")
        self.completed_label.grid(row=1, column=0, sticky="w", padx=10, pady=5)

        self.failed_label = ctk.CTkLabel(self.stats_frame, text="Failed: 0")
        self.failed_label.grid(row=2, column=0, sticky="w", padx=10, pady=5)

        self.speed_label = ctk.CTkLabel(self.stats_frame, text="Speed: 0 files/s")
        self.speed_label.grid(row=3, column=0, sticky="w", padx=10, pady=5)

        self.success_rate_label = ctk.CTkLabel(self.stats_frame, text="Success Rate: 0%")
        self.success_rate_label.grid(row=4, column=0, sticky="w", padx=10, pady=5)

        self.eta_label = ctk.CTkLabel(self.stats_frame, text="ETA: --")
        self.eta_label.grid(row=5, column=0, sticky="w", padx=10, pady=5)

        # Progress bar
        self.progress_bar = ctk.CTkProgressBar(self)
        self.progress_bar.pack(fill="x", padx=10, pady=10)
        self.progress_bar.set(0)

    def update_statistics(self, stats: BatchStatistics) -> None:
        """
        Update statistics display.
        
        Args:
            stats: Batch statistics
        """
        self.total_label.configure(text=f"Total: {stats.total_tasks}")
        self.completed_label.configure(text=f"Completed: {stats.completed_tasks}")
        self.failed_label.configure(text=f"Failed: {stats.failed_tasks}")
        self.speed_label.configure(text=f"Speed: {stats.processing_speed:.2f} files/s")
        self.success_rate_label.configure(text=f"Success Rate: {stats.success_rate:.1f}%")

        if stats.estimated_time_remaining:
            eta_str = str(stats.estimated_time_remaining).split('.')[0]
            self.eta_label.configure(text=f"ETA: {eta_str}")
        else:
            self.eta_label.configure(text="ETA: --")

        self.progress_bar.set(stats.progress_percentage / 100)


class BatchControlPanel(ctk.CTkFrame):
    """Control panel for batch processing."""

    def __init__(
        self,
        master: Any,
        on_pause: Optional[Callable[[], None]] = None,
        on_resume: Optional[Callable[[], None]] = None,
        on_cancel_all: Optional[Callable[[], None]] = None,
        **kwargs
    ) -> None:
        """
        Initialize control panel.
        
        Args:
            master: Parent widget
            on_pause: Callback for pause
            on_resume: Callback for resume
            on_cancel_all: Callback for cancel all
            **kwargs: Additional CTkFrame arguments
        """
        super().__init__(master, **kwargs)
        self.on_pause = on_pause
        self.on_resume = on_resume
        self.on_cancel_all = on_cancel_all
        self.is_paused = False

        self._create_widgets()

    def _create_widgets(self) -> None:
        """Create control widgets."""
        title = ctk.CTkLabel(
            self,
            text="Batch Controls",
            font=ctk.CTkFont(size=14, weight="bold"),
        )
        title.pack(pady=10)

        # Control buttons
        self.pause_button = ctk.CTkButton(
            self,
            text="Pause",
            command=self._on_pause_clicked,
            width=100,
        )
        self.pause_button.pack(pady=5)

        self.resume_button = ctk.CTkButton(
            self,
            text="Resume",
            command=self._on_resume_clicked,
            width=100,
            state="disabled",
        )
        self.resume_button.pack(pady=5)

        self.cancel_button = ctk.CTkButton(
            self,
            text="Cancel All",
            command=self._on_cancel_clicked,
            width=100,
            fg_color=("red", "darkred"),
            hover_color=("darkred", "red"),
        )
        self.cancel_button.pack(pady=5)

    def _on_pause_clicked(self) -> None:
        """Handle pause button click."""
        self.is_paused = True
        self.pause_button.configure(state="disabled")
        self.resume_button.configure(state="normal")
        if self.on_pause:
            self.on_pause()

    def _on_resume_clicked(self) -> None:
        """Handle resume button click."""
        self.is_paused = False
        self.pause_button.configure(state="normal")
        self.resume_button.configure(state="disabled")
        if self.on_resume:
            self.on_resume()

    def _on_cancel_clicked(self) -> None:
        """Handle cancel button click."""
        if self.on_cancel_all:
            self.on_cancel_all()


class BatchTaskList(ctk.CTkFrame):
    """List of batch tasks with status."""

    def __init__(self, master: Any, **kwargs) -> None:
        """Initialize task list."""
        super().__init__(master, **kwargs)
        self.tasks: Dict[str, ctk.CTkFrame] = {}
        self._create_widgets()

    def _create_widgets(self) -> None:
        """Create task list widgets."""
        title = ctk.CTkLabel(
            self,
            text="Tasks",
            font=ctk.CTkFont(size=14, weight="bold"),
        )
        title.pack(pady=10)

        # Scrollable frame
        self.scrollable_frame = ctk.CTkScrollableFrame(self)
        self.scrollable_frame.pack(fill="both", expand=True, padx=10, pady=10)

    def add_task(self, task: BatchTask) -> None:
        """
        Add task to list.
        
        Args:
            task: Batch task
        """
        task_frame = ctk.CTkFrame(self.scrollable_frame)
        task_frame.pack(fill="x", padx=5, pady=2)

        # Status indicator
        status_colors = {
            TaskStatus.PENDING: ("gray60", "gray40"),
            TaskStatus.QUEUED: ("blue", "blue"),
            TaskStatus.PROCESSING: ("#3498DB", "#3498DB"),
            TaskStatus.COMPLETED: ("#2ECC71", "#2ECC71"),
            TaskStatus.FAILED: ("#E74C3C", "#E74C3C"),
            TaskStatus.CANCELLED: ("gray60", "gray40"),
            TaskStatus.RETRYING: ("#F39C12", "#F39C12"),
        }
        color = status_colors.get(task.status, ("gray60", "gray40"))

        status_indicator = ctk.CTkLabel(
            task_frame,
            text="●",
            width=20,
            fg_color=color,
        )
        status_indicator.pack(side="left", padx=5)

        # File name
        name_label = ctk.CTkLabel(
            task_frame,
            text=task.input_file.name,
            anchor="w",
        )
        name_label.pack(side="left", padx=5, fill="x", expand=True)

        # Status text
        status_label = ctk.CTkLabel(
            task_frame,
            text=task.status.value,
            width=100,
        )
        status_label.pack(side="right", padx=5)

        self.tasks[task.task_id] = task_frame

    def update_task(self, task: BatchTask) -> None:
        """
        Update task in list.
        
        Args:
            task: Updated task
        """
        if task.task_id in self.tasks:
            # Recreate task frame with updated status
            self.tasks[task.task_id].destroy()
            self.add_task(task)

