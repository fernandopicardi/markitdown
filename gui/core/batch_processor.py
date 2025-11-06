"""
Batch processing system for MarkItDown GUI.

This module provides robust batch conversion with queue management,
parallel processing, retry logic, and advanced filtering.
"""

import asyncio
import logging
import time
import hashlib
from pathlib import Path
from typing import List, Dict, Optional, Callable, Any, Set, Awaitable
from dataclasses import dataclass, field
from enum import Enum
from datetime import datetime, timedelta
from concurrent.futures import ThreadPoolExecutor, ProcessPoolExecutor, Future, as_completed
import queue
import threading
import re
import multiprocessing
from functools import partial

from gui.core.events import Event, EventType, EventBus
from gui.core.state import ConversionState, ConversionStatus

logger = logging.getLogger(__name__)


class TaskPriority(Enum):
    """Task priority levels."""

    LOW = 0
    NORMAL = 1
    HIGH = 2
    URGENT = 3


class TaskStatus(Enum):
    """Task status."""

    PENDING = "pending"
    QUEUED = "queued"
    PROCESSING = "processing"
    COMPLETED = "completed"
    FAILED = "failed"
    CANCELLED = "cancelled"
    RETRYING = "retrying"


@dataclass
class BatchTask:
    """Represents a single batch conversion task."""

    task_id: str = field(default_factory=lambda: f"task_{int(time.time() * 1000)}")
    input_file: Path = None
    output_file: Optional[Path] = None
    priority: TaskPriority = TaskPriority.NORMAL
    status: TaskStatus = TaskStatus.PENDING
    retry_count: int = 0
    max_retries: int = 3
    created_at: datetime = field(default_factory=datetime.now)
    started_at: Optional[datetime] = None
    completed_at: Optional[datetime] = None
    error_message: Optional[str] = None
    result_text: Optional[str] = None
    file_hash: Optional[str] = None  # For duplicate detection

    def __post_init__(self) -> None:
        """Calculate file hash for duplicate detection."""
        if self.input_file and self.input_file.exists():
            try:
                with open(self.input_file, "rb") as f:
                    file_hash = hashlib.md5(f.read(1024 * 1024)).hexdigest()  # First 1MB
                    self.file_hash = file_hash
            except Exception as e:
                logger.warning(f"Failed to calculate hash for {self.input_file}: {e}")

    def __lt__(self, other: "BatchTask") -> bool:
        """Compare tasks for priority queue (higher priority first)."""
        if self.priority.value != other.priority.value:
            return self.priority.value > other.priority.value
        return self.created_at < other.created_at


@dataclass
class BatchStatistics:
    """Statistics for batch processing."""

    total_tasks: int = 0
    completed_tasks: int = 0
    failed_tasks: int = 0
    cancelled_tasks: int = 0
    retry_count: int = 0
    total_files_size: int = 0  # bytes
    processed_size: int = 0  # bytes
    start_time: Optional[datetime] = None
    end_time: Optional[datetime] = None
    tasks_by_status: Dict[TaskStatus, int] = field(default_factory=lambda: {
        status: 0 for status in TaskStatus
    })

    @property
    def success_rate(self) -> float:
        """Calculate success rate."""
        if self.total_tasks == 0:
            return 0.0
        return (self.completed_tasks / self.total_tasks) * 100

    @property
    def processing_speed(self) -> float:
        """Calculate processing speed (files per second)."""
        if not self.start_time:
            return 0.0
        elapsed = (datetime.now() - self.start_time).total_seconds()
        if elapsed == 0:
            return 0.0
        return self.completed_tasks / elapsed

    @property
    def estimated_time_remaining(self) -> Optional[timedelta]:
        """Estimate time remaining."""
        if self.total_tasks == 0 or self.completed_tasks == 0:
            return None

        remaining = self.total_tasks - self.completed_tasks
        if self.processing_speed == 0:
            return None

        seconds_remaining = remaining / self.processing_speed
        return timedelta(seconds=seconds_remaining)

    @property
    def progress_percentage(self) -> float:
        """Calculate progress percentage."""
        if self.total_tasks == 0:
            return 0.0
        return (self.completed_tasks / self.total_tasks) * 100


class FileFilter:
    """Advanced file filtering system."""

    def __init__(
        self,
        extensions: Optional[List[str]] = None,
        min_size: Optional[int] = None,  # bytes
        max_size: Optional[int] = None,  # bytes
        min_date: Optional[datetime] = None,
        max_date: Optional[datetime] = None,
        name_pattern: Optional[str] = None,  # regex
        exclude_paths: Optional[List[Path]] = None,
        exclude_patterns: Optional[List[str]] = None,  # regex patterns
    ) -> None:
        """
        Initialize file filter.
        
        Args:
            extensions: Allowed file extensions (e.g., ['.pdf', '.docx'])
            min_size: Minimum file size in bytes
            max_size: Maximum file size in bytes
            min_date: Minimum modification date
            max_date: Maximum modification date
            name_pattern: Regex pattern for filename matching
            exclude_paths: Paths to exclude
            exclude_patterns: Regex patterns for paths to exclude
        """
        self.extensions = extensions
        self.min_size = min_size
        self.max_size = max_size
        self.min_date = min_date
        self.max_date = max_date
        self.name_pattern = re.compile(name_pattern) if name_pattern else None
        self.exclude_paths = exclude_paths or []
        self.exclude_patterns = [re.compile(p) for p in (exclude_patterns or [])]

    def matches(self, file_path: Path) -> bool:
        """
        Check if file matches filter criteria.
        
        Args:
            file_path: File path to check
            
        Returns:
            True if file matches, False otherwise
        """
        # Check extension
        if self.extensions:
            if file_path.suffix.lower() not in [e.lower() for e in self.extensions]:
                return False

        # Check size
        try:
            file_size = file_path.stat().st_size
            if self.min_size and file_size < self.min_size:
                return False
            if self.max_size and file_size > self.max_size:
                return False
        except Exception:
            return False

        # Check modification date
        try:
            mod_time = datetime.fromtimestamp(file_path.stat().st_mtime)
            if self.min_date and mod_time < self.min_date:
                return False
            if self.max_date and mod_time > self.max_date:
                return False
        except Exception:
            return False

        # Check name pattern
        if self.name_pattern:
            if not self.name_pattern.search(file_path.name):
                return False

        # Check exclude paths
        for exclude_path in self.exclude_paths:
            try:
                if exclude_path.resolve() in file_path.resolve().parents:
                    return False
                if file_path.resolve() == exclude_path.resolve():
                    return False
            except Exception:
                pass

        # Check exclude patterns
        file_str = str(file_path)
        for pattern in self.exclude_patterns:
            if pattern.search(file_str):
                return False

        return True

    def filter_files(self, file_paths: List[Path]) -> List[Path]:
        """
        Filter list of files.
        
        Args:
            file_paths: List of file paths to filter
            
        Returns:
            Filtered list of file paths
        """
        return [fp for fp in file_paths if self.matches(fp)]


class BatchProcessor:
    """
    Batch processor with queue management and parallel execution.
    
    Features:
    - Priority queue
    - Parallel processing
    - Pause/resume
    - Cancel operations
    - Retry with backoff
    - Duplicate detection
    - File filtering
    - Statistics tracking
    """

    def __init__(
        self,
        event_bus: EventBus,
        max_workers: int = 4,
        use_processes: bool = False,
        conversion_func: Optional[Callable] = None,
        async_conversion_func: Optional[Callable[[str, Optional[str]], Awaitable[Any]]] = None,
    ) -> None:
        """
        Initialize batch processor.
        
        Args:
            event_bus: Event bus for notifications
            max_workers: Maximum number of worker threads/processes
            use_processes: Use ProcessPoolExecutor for CPU-bound operations
            conversion_func: Synchronous function to perform conversion
            async_conversion_func: Async function to perform conversion (for I/O-bound)
        """
        self.event_bus = event_bus
        self.max_workers = max_workers
        self.use_processes = use_processes
        self.conversion_func = conversion_func
        self.async_conversion_func = async_conversion_func

        # Queue and executor
        self.task_queue: queue.PriorityQueue = queue.PriorityQueue()
        self.executor: Optional[ThreadPoolExecutor | ProcessPoolExecutor] = None
        self.futures: Dict[str, Future] = {}
        self.async_tasks: Dict[str, asyncio.Future] = {}  # run_coroutine_threadsafe returns Future

        # State management
        self.is_paused = False
        self.is_cancelled = False
        self.pause_event = threading.Event()
        self.pause_event.set()  # Initially not paused

        # Tasks and statistics
        self.tasks: Dict[str, BatchTask] = {}
        self.statistics = BatchStatistics()
        self.duplicate_hashes: Set[str] = set()

        # Worker thread and async loop
        self.worker_thread: Optional[threading.Thread] = None
        self.async_loop: Optional[asyncio.AbstractEventLoop] = None
        self.async_thread: Optional[threading.Thread] = None
        self.running = False

        # Determine if using async
        self.use_async = async_conversion_func is not None

        logger.info(f"BatchProcessor initialized with {max_workers} workers (async={self.use_async}, processes={use_processes})")

    def add_task(
        self,
        input_file: Path,
        output_file: Optional[Path] = None,
        priority: TaskPriority = TaskPriority.NORMAL,
        max_retries: int = 3,
    ) -> BatchTask:
        """
        Add a task to the queue.
        
        Args:
            input_file: Input file path
            output_file: Optional output file path
            priority: Task priority
            max_retries: Maximum retry attempts
            
        Returns:
            Created BatchTask
        """
        task = BatchTask(
            input_file=input_file,
            output_file=output_file,
            priority=priority,
            max_retries=max_retries,
        )

        # Check for duplicates
        if task.file_hash and task.file_hash in self.duplicate_hashes:
            logger.debug(f"Duplicate detected: {input_file}")
            task.status = TaskStatus.CANCELLED
            task.error_message = "Duplicate file"
            self.statistics.cancelled_tasks += 1
            return task

        self.tasks[task.task_id] = task
        self.task_queue.put(task)
        if task.file_hash:
            self.duplicate_hashes.add(task.file_hash)

        self.statistics.total_tasks += 1
        self.statistics.tasks_by_status[TaskStatus.QUEUED] += 1
        task.status = TaskStatus.QUEUED

        self.event_bus.emit(Event(
            EventType.CONVERSION_STARTED,
            {"task_id": task.task_id, "input_file": str(input_file)},
            source="BatchProcessor"
        ))

        logger.info(f"Task added: {input_file} (priority: {priority.name})")
        return task

    def add_files(
        self,
        file_paths: List[Path],
        output_dir: Optional[Path] = None,
        file_filter: Optional[FileFilter] = None,
        priority: TaskPriority = TaskPriority.NORMAL,
    ) -> List[BatchTask]:
        """
        Add multiple files to the queue.
        
        Args:
            file_paths: List of file paths
            output_dir: Optional output directory
            file_filter: Optional file filter
            priority: Task priority
            
        Returns:
            List of created tasks
        """
        # Filter files
        if file_filter:
            file_paths = file_filter.filter_files(file_paths)

        tasks = []
        for file_path in file_paths:
            output_file = None
            if output_dir:
                output_file = output_dir / file_path.with_suffix('.md').name

            task = self.add_task(
                input_file=file_path,
                output_file=output_file,
                priority=priority,
                max_retries=max_retries,
            )
            tasks.append(task)

        return tasks

    def start(self) -> None:
        """Start batch processing."""
        if self.running:
            logger.warning("Batch processor already running")
            return

        self.running = True
        self.is_paused = False
        self.is_cancelled = False
        self.pause_event.set()

        # Create executor for CPU-bound operations
        if self.use_processes:
            self.executor = ProcessPoolExecutor(max_workers=self.max_workers)
        else:
            self.executor = ThreadPoolExecutor(max_workers=self.max_workers)

        # Start async loop if using async
        if self.use_async:
            self._start_async_loop()

        # Start worker thread
        self.worker_thread = threading.Thread(target=self._worker_loop, daemon=True)
        self.worker_thread.start()

        self.statistics.start_time = datetime.now()
        logger.info("Batch processor started")

    def _start_async_loop(self) -> None:
        """Start async event loop in separate thread."""
        def run_async_loop():
            self.async_loop = asyncio.new_event_loop()
            asyncio.set_event_loop(self.async_loop)
            self.async_loop.run_forever()

        self.async_thread = threading.Thread(target=run_async_loop, daemon=True)
        self.async_thread.start()
        # Wait for loop to be ready
        time.sleep(0.1)

    def pause(self) -> None:
        """Pause batch processing."""
        self.is_paused = True
        self.pause_event.clear()
        logger.info("Batch processing paused")

    def resume(self) -> None:
        """Resume batch processing."""
        self.is_paused = False
        self.pause_event.set()
        logger.info("Batch processing resumed")

    def cancel_all(self) -> None:
        """Cancel all pending and processing tasks."""
        self.is_cancelled = True

        # Cancel futures
        for task_id, future in list(self.futures.items()):
            if not future.done():
                future.cancel()
                if task_id in self.tasks:
                    self.tasks[task_id].status = TaskStatus.CANCELLED
                    self.statistics.cancelled_tasks += 1

        self.futures.clear()

        # Cancel async tasks
        if self.async_loop:
            for task_id, async_task in list(self.async_tasks.items()):
                if not async_task.done():
                    async_task.cancel()
                    if task_id in self.tasks:
                        self.tasks[task_id].status = TaskStatus.CANCELLED
                        self.statistics.cancelled_tasks += 1

        self.async_tasks.clear()

        # Clear queue
        while not self.task_queue.empty():
            try:
                task = self.task_queue.get_nowait()
                task.status = TaskStatus.CANCELLED
                self.statistics.cancelled_tasks += 1
            except queue.Empty:
                break

        logger.info("All tasks cancelled")

    def cancel_task(self, task_id: str) -> bool:
        """
        Cancel a specific task.
        
        Args:
            task_id: Task ID to cancel
            
        Returns:
            True if cancelled, False if not found
        """
        # Cancel future if exists
        if task_id in self.futures:
            future = self.futures[task_id]
            if not future.done():
                future.cancel()
                if task_id in self.tasks:
                    self.tasks[task_id].status = TaskStatus.CANCELLED
                    self.statistics.cancelled_tasks += 1
                del self.futures[task_id]
                return True

        # Cancel async task if exists
        if task_id in self.async_tasks:
            async_task = self.async_tasks[task_id]
            if not async_task.done():
                async_task.cancel()
                if task_id in self.tasks:
                    self.tasks[task_id].status = TaskStatus.CANCELLED
                    self.statistics.cancelled_tasks += 1
                del self.async_tasks[task_id]
                return True

        # Check if in queue
        if task_id in self.tasks:
            task = self.tasks[task_id]
            if task.status == TaskStatus.QUEUED:
                task.status = TaskStatus.CANCELLED
                self.statistics.cancelled_tasks += 1
                return True

        return False

    def stop(self) -> None:
        """Stop batch processing."""
        self.running = False
        self.cancel_all()

        # Cancel async tasks
        if self.async_loop:
            for task_id, async_task in list(self.async_tasks.items()):
                if not async_task.done():
                    async_task.cancel()

        if self.executor:
            self.executor.shutdown(wait=True)

        # Stop async loop
        if self.async_loop:
            self.async_loop.call_soon_threadsafe(self.async_loop.stop)
            if self.async_thread:
                self.async_thread.join(timeout=2.0)

        if self.worker_thread:
            self.worker_thread.join(timeout=5.0)

        self.statistics.end_time = datetime.now()
        logger.info("Batch processor stopped")

    def _worker_loop(self) -> None:
        """Main worker loop."""
        while self.running:
            try:
                # Wait for pause event
                self.pause_event.wait()

                if self.is_cancelled:
                    break

                # Get task from queue
                try:
                    task = self.task_queue.get(timeout=1.0)
                except queue.Empty:
                    continue

                # Check if cancelled
                if self.is_cancelled or task.status == TaskStatus.CANCELLED:
                    continue

                # Submit task
                task.status = TaskStatus.PROCESSING
                task.started_at = datetime.now()
                self.statistics.tasks_by_status[TaskStatus.QUEUED] -= 1
                self.statistics.tasks_by_status[TaskStatus.PROCESSING] += 1

                # Use async for I/O-bound, executor for CPU-bound
                if self.use_async and self.async_loop:
                    # Submit async task
                    async_task = asyncio.run_coroutine_threadsafe(
                        self._process_task_async(task),
                        self.async_loop
                    )
                    self.async_tasks[task.task_id] = async_task
                    # Handle async task completion
                    self._handle_async_task(task, async_task)
                else:
                    # Use executor for CPU-bound or sync operations
                    if self.use_processes:
                        # CPU-bound: use ProcessPoolExecutor
                        future = self.executor.submit(self._process_task_cpu_bound, task)
                    else:
                        # I/O-bound: use ThreadPoolExecutor
                        future = self.executor.submit(self._process_task, task)
                    self.futures[task.task_id] = future
                    # Handle future completion
                    self._handle_future(task, future)

            except Exception as e:
                logger.error(f"Error in worker loop: {e}", exc_info=True)

    async def _process_task_async(self, task: BatchTask) -> Dict[str, Any]:
        """
        Process a single task asynchronously (for I/O-bound operations).
        
        Args:
            task: Task to process
            
        Returns:
            Result dictionary
        """
        if not self.async_conversion_func:
            raise ValueError("No async conversion function provided")

        try:
            # Check if cancelled
            if self.is_cancelled or task.status == TaskStatus.CANCELLED:
                return {
                    "success": False,
                    "result_text": None,
                    "error": "Task cancelled",
                }

            # Run async conversion
            result = await self.async_conversion_func(
                str(task.input_file),
                str(task.output_file) if task.output_file else None
            )
            
            # Handle different result types
            if isinstance(result, dict):
                result_text = result.get("text_content", "")
            elif hasattr(result, "text_content"):
                result_text = result.text_content
            else:
                result_text = str(result)

            return {
                "success": True,
                "result_text": result_text,
                "error": None,
            }
        except Exception as e:
            return {
                "success": False,
                "result_text": None,
                "error": str(e),
            }

    def _process_task(self, task: BatchTask) -> Dict[str, Any]:
        """
        Process a single task synchronously (for I/O-bound in thread).
        
        Args:
            task: Task to process
            
        Returns:
            Result dictionary
        """
        if not self.conversion_func:
            raise ValueError("No conversion function provided")

        try:
            # Check if cancelled
            if self.is_cancelled or task.status == TaskStatus.CANCELLED:
                return {
                    "success": False,
                    "result_text": None,
                    "error": "Task cancelled",
                }

            result = self.conversion_func(
                str(task.input_file),
                str(task.output_file) if task.output_file else None
            )
            
            # Handle different result types
            if isinstance(result, dict):
                result_text = result.get("text_content", "")
            elif hasattr(result, "text_content"):
                result_text = result.text_content
            else:
                result_text = str(result)

            return {
                "success": True,
                "result_text": result_text,
                "error": None,
            }
        except Exception as e:
            return {
                "success": False,
                "result_text": None,
                "error": str(e),
            }

    def _process_task_cpu_bound(self, task: BatchTask) -> Dict[str, Any]:
        """
        Process a single task in separate process (for CPU-bound operations).
        
        Args:
            task: Task to process
            
        Returns:
            Result dictionary
        """
        # This runs in a separate process, so we need to import here
        try:
            from markitdown import MarkItDown
            
            # Check if cancelled
            if self.is_cancelled:
                return {
                    "success": False,
                    "result_text": None,
                    "error": "Task cancelled",
                }

            # Create MarkItDown instance in process
            md = MarkItDown()
            result = md.convert(str(task.input_file))
            
            return {
                "success": True,
                "result_text": result.text_content,
                "error": None,
            }
        except Exception as e:
            return {
                "success": False,
                "result_text": None,
                "error": str(e),
            }

    def _handle_future(self, task: BatchTask, future: Future) -> None:
        """Handle future completion (for sync operations)."""
        # Monitor future in background thread
        def monitor_future():
            try:
                result = future.result(timeout=300)  # 5 minute timeout
                self._handle_task_result(task, result)
            except Exception as e:
                task.status = TaskStatus.FAILED
                task.error_message = str(e)
                task.completed_at = datetime.now()
                self.statistics.failed_tasks += 1
                if TaskStatus.PROCESSING in self.statistics.tasks_by_status:
                    self.statistics.tasks_by_status[TaskStatus.PROCESSING] = max(
                        0, self.statistics.tasks_by_status[TaskStatus.PROCESSING] - 1
                    )
                self.statistics.tasks_by_status[TaskStatus.FAILED] += 1
                logger.error(f"Task {task.task_id} failed: {e}")
            finally:
                if task.task_id in self.futures:
                    del self.futures[task.task_id]

        # Start monitoring in background
        threading.Thread(target=monitor_future, daemon=True).start()

    def _handle_async_task(self, task: BatchTask, async_task: asyncio.Future) -> None:
        """Handle async task completion."""
        def on_complete(future: asyncio.Future) -> None:
            """Callback when async task completes."""
            try:
                result = future.result()
                # Handle result same as sync version
                self._handle_task_result(task, result)
            except asyncio.CancelledError:
                task.status = TaskStatus.CANCELLED
                self.statistics.cancelled_tasks += 1
                if TaskStatus.PROCESSING in self.statistics.tasks_by_status:
                    self.statistics.tasks_by_status[TaskStatus.PROCESSING] = max(
                        0, self.statistics.tasks_by_status[TaskStatus.PROCESSING] - 1
                    )
                logger.info(f"Async task {task.task_id} cancelled")
            except Exception as e:
                task.status = TaskStatus.FAILED
                task.error_message = str(e)
                task.completed_at = datetime.now()
                self.statistics.failed_tasks += 1
                if TaskStatus.PROCESSING in self.statistics.tasks_by_status:
                    self.statistics.tasks_by_status[TaskStatus.PROCESSING] = max(
                        0, self.statistics.tasks_by_status[TaskStatus.PROCESSING] - 1
                    )
                self.statistics.tasks_by_status[TaskStatus.FAILED] += 1
                logger.error(f"Async task {task.task_id} failed: {e}")
            finally:
                if task.task_id in self.async_tasks:
                    del self.async_tasks[task.task_id]

        # Add callback
        async_task.add_done_callback(on_complete)

    def _handle_task_result(self, task: BatchTask, result: Dict[str, Any]) -> None:
        """Handle task result (shared for sync and async)."""
        if result["success"]:
            task.status = TaskStatus.COMPLETED
            task.result_text = result["result_text"]
            task.completed_at = datetime.now()

            # Save result if output file specified
            if task.output_file:
                try:
                    task.output_file.parent.mkdir(parents=True, exist_ok=True)
                    task.output_file.write_text(task.result_text, encoding='utf-8')
                except Exception as e:
                    logger.error(f"Failed to save result for {task.task_id}: {e}")

            self.statistics.completed_tasks += 1
            self.statistics.tasks_by_status[TaskStatus.PROCESSING] -= 1
            self.statistics.tasks_by_status[TaskStatus.COMPLETED] += 1

            self.event_bus.emit(Event(
                EventType.CONVERSION_COMPLETED,
                {"task_id": task.task_id, "input_file": str(task.input_file)},
                source="BatchProcessor"
            ))
        else:
            # Retry logic
            if task.retry_count < task.max_retries and not self.is_cancelled:
                task.retry_count += 1
                task.status = TaskStatus.RETRYING
                self.statistics.retry_count += 1
                self.statistics.tasks_by_status[TaskStatus.PROCESSING] -= 1

                # Exponential backoff
                delay = 2 ** task.retry_count
                logger.info(f"Retrying task {task.task_id} (attempt {task.retry_count}/{task.max_retries}) after {delay}s")

                # Re-queue task after delay
                def requeue_after_delay():
                    time.sleep(delay)
                    if not self.is_cancelled and task.status == TaskStatus.RETRYING:
                        task.status = TaskStatus.QUEUED
                        self.task_queue.put(task)
                        self.statistics.tasks_by_status[TaskStatus.QUEUED] += 1

                threading.Thread(target=requeue_after_delay, daemon=True).start()
            else:
                task.status = TaskStatus.FAILED
                task.error_message = result["error"]
                task.completed_at = datetime.now()
                self.statistics.failed_tasks += 1
                self.statistics.tasks_by_status[TaskStatus.PROCESSING] -= 1
                self.statistics.tasks_by_status[TaskStatus.FAILED] += 1

                self.event_bus.emit(Event(
                    EventType.CONVERSION_FAILED,
                    {"task_id": task.task_id, "error": result["error"]},
                    source="BatchProcessor"
                ))

    def get_statistics(self) -> BatchStatistics:
        """
        Get current statistics.
        
        Returns:
            Current batch statistics
        """
        return self.statistics

    def get_task(self, task_id: str) -> Optional[BatchTask]:
        """
        Get task by ID.
        
        Args:
            task_id: Task ID
            
        Returns:
            Task or None
        """
        return self.tasks.get(task_id)

    def get_all_tasks(self) -> List[BatchTask]:
        """
        Get all tasks.
        
        Returns:
            List of all tasks
        """
        return list(self.tasks.values())

