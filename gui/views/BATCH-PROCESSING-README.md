# Batch Processing System

## Overview

The MarkItDown GUI features a robust batch processing system that allows converting multiple files simultaneously with advanced queue management, parallel processing, filtering, and real-time statistics.

## Features

### ✅ Queue Management
- **Priority Queue**: Tasks processed by priority (LOW, NORMAL, HIGH, URGENT)
- **Task Management**: Add, remove, cancel individual tasks
- **Queue Status**: Real-time queue monitoring

### ✅ Parallel Processing
- **ThreadPoolExecutor**: For I/O-bound operations (default)
- **ProcessPoolExecutor**: For CPU-bound operations (optional)
- **Configurable Workers**: Set maximum number of concurrent workers
- **Efficient Resource Usage**: Optimal thread/process management

### ✅ Pause/Resume
- **Pause Processing**: Temporarily halt batch processing
- **Resume Processing**: Continue from where it paused
- **State Preservation**: Tasks maintain their state during pause

### ✅ Cancel Operations
- **Cancel Individual**: Cancel specific tasks
- **Cancel All**: Cancel all pending and processing tasks
- **Graceful Cancellation**: Proper cleanup of resources

### ✅ Retry with Exponential Backoff
- **Automatic Retry**: Failed tasks retry automatically
- **Configurable Retries**: Set maximum retry attempts per task
- **Exponential Backoff**: Delay increases exponentially (2^retry_count seconds)
- **Retry Status**: Visual indication of retrying tasks

### ✅ Duplicate Detection
- **File Hashing**: MD5 hash of first 1MB for duplicate detection
- **Automatic Skip**: Duplicate files automatically skipped
- **Hash Tracking**: Maintains set of processed file hashes

### ✅ Advanced File Filtering

#### By Extension
```python
filter = FileFilter(extensions=['.pdf', '.docx', '.pptx'])
```

#### By Size
```python
filter = FileFilter(
    min_size=1024 * 1024,  # 1 MB minimum
    max_size=100 * 1024 * 1024  # 100 MB maximum
)
```

#### By Date
```python
from datetime import datetime, timedelta

filter = FileFilter(
    min_date=datetime.now() - timedelta(days=30),  # Last 30 days
    max_date=datetime.now()
)
```

#### By Name Pattern (Regex)
```python
filter = FileFilter(name_pattern=r'^report_\d+\.pdf$')
```

#### Exclude Paths
```python
filter = FileFilter(
    exclude_paths=[
        Path('/path/to/exclude'),
        Path('/another/path'),
    ]
)
```

#### Exclude Patterns (Regex)
```python
filter = FileFilter(
    exclude_patterns=[
        r'.*temp.*',
        r'.*backup.*',
    ]
)
```

### ✅ Preview Before Processing
- **File List Preview**: See all files before starting
- **Filter Results**: Preview filtered file list
- **Count Display**: Total number of files to process
- **Start Confirmation**: Review before processing

### ✅ Time Estimation
- **ETA Calculation**: Estimated time remaining
- **Processing Speed**: Files per second
- **Progress Tracking**: Real-time progress updates
- **Time Remaining**: Based on current processing speed

### ✅ Real-time Statistics
- **Total Tasks**: Number of tasks in queue
- **Completed**: Successfully completed tasks
- **Failed**: Failed tasks count
- **Cancelled**: Cancelled tasks count
- **Success Rate**: Percentage of successful conversions
- **Processing Speed**: Files processed per second
- **ETA**: Estimated time to completion
- **Progress Bar**: Visual progress indicator

## Usage

### Basic Batch Processing

```python
from gui.core.batch_processor import BatchProcessor, FileFilter, TaskPriority
from gui.core.events import EventBus
from pathlib import Path

event_bus = EventBus()

# Create processor
processor = BatchProcessor(
    event_bus=event_bus,
    max_workers=4,
    use_processes=False,
    conversion_func=conversion_function,
)

# Add files
files = [Path("file1.pdf"), Path("file2.docx")]
tasks = processor.add_files(
    file_paths=files,
    output_dir=Path("output"),
    priority=TaskPriority.NORMAL,
)

# Start processing
processor.start()
```

### With File Filtering

```python
from gui.core.batch_processor import FileFilter

# Create filter
filter = FileFilter(
    extensions=['.pdf', '.docx'],
    min_size=1024 * 1024,  # 1 MB
    max_size=100 * 1024 * 1024,  # 100 MB
    name_pattern=r'^report.*\.pdf$',
    exclude_paths=[Path('/exclude/this')],
)

# Add files with filter
tasks = processor.add_files(
    file_paths=all_files,
    output_dir=Path("output"),
    file_filter=filter,
)
```

### Control Processing

```python
# Pause
processor.pause()

# Resume
processor.resume()

# Cancel all
processor.cancel_all()

# Cancel specific task
processor.cancel_task(task_id)

# Stop processor
processor.stop()
```

### Get Statistics

```python
stats = processor.get_statistics()

print(f"Total: {stats.total_tasks}")
print(f"Completed: {stats.completed_tasks}")
print(f"Failed: {stats.failed_tasks}")
print(f"Success Rate: {stats.success_rate:.1f}%")
print(f"Speed: {stats.processing_speed:.2f} files/s")
print(f"ETA: {stats.estimated_time_remaining}")
```

### Using Batch Window

```python
from gui.views.batch_window import BatchProcessingWindow
from gui.core.events import EventBus
from gui.models.conversion_model import ConversionModel

event_bus = EventBus()
conversion_model = ConversionModel(event_bus=event_bus)

window = BatchProcessingWindow(
    event_bus=event_bus,
    conversion_model=conversion_model,
)
window.run()
```

## Architecture

### BatchProcessor
- Manages task queue
- Handles parallel execution
- Tracks statistics
- Manages retry logic

### FileFilter
- Advanced filtering system
- Multiple filter criteria
- Regex pattern matching
- Path exclusion

### BatchTask
- Individual task representation
- Priority and status tracking
- Retry management
- Result storage

### BatchStatistics
- Real-time statistics
- Progress calculation
- Speed estimation
- ETA calculation

## Task Priority

Tasks are processed in priority order:

1. **URGENT** (3): Highest priority
2. **HIGH** (2): High priority
3. **NORMAL** (1): Default priority
4. **LOW** (0): Lowest priority

Within same priority, older tasks are processed first.

## Retry Logic

### Exponential Backoff

Retry delays increase exponentially:
- 1st retry: 2 seconds
- 2nd retry: 4 seconds
- 3rd retry: 8 seconds
- etc.

### Retry Configuration

```python
task = processor.add_task(
    input_file=Path("file.pdf"),
    max_retries=5,  # Maximum retry attempts
)
```

## Duplicate Detection

Files are hashed (first 1MB) to detect duplicates:

```python
# Automatic duplicate detection
# Duplicate files are automatically skipped
# Hash is calculated on task creation
```

## Performance

### ThreadPoolExecutor (Default)
- Best for I/O-bound operations
- Lower memory overhead
- Faster startup
- Good for file I/O

### ProcessPoolExecutor (Optional)
- Best for CPU-bound operations
- True parallelism
- Higher memory overhead
- Better for CPU-intensive conversions

### Worker Configuration

```python
# 4 workers (default)
processor = BatchProcessor(max_workers=4)

# 8 workers for faster processing
processor = BatchProcessor(max_workers=8)

# Use processes for CPU-bound
processor = BatchProcessor(
    max_workers=4,
    use_processes=True,
)
```

## Statistics

### Real-time Metrics

- **Total Tasks**: All tasks in batch
- **Completed**: Successfully completed
- **Failed**: Failed after all retries
- **Cancelled**: User-cancelled tasks
- **Retry Count**: Total retry attempts
- **Success Rate**: Percentage successful
- **Processing Speed**: Files/second
- **ETA**: Estimated time remaining
- **Progress**: Percentage complete

### Statistics Updates

Statistics update every second during processing.

## Best Practices

1. **Filter First**: Use filters to reduce task count
2. **Preview**: Always preview before processing
3. **Monitor**: Watch statistics during processing
4. **Pause if Needed**: Pause to investigate issues
5. **Retry Configuration**: Set appropriate retry limits
6. **Worker Count**: Balance speed vs. resource usage
7. **Output Directory**: Use dedicated output directory

## Troubleshooting

### Slow Processing
- Increase worker count
- Check file sizes
- Verify filters aren't too restrictive
- Check system resources

### High Failure Rate
- Check file formats
- Verify file accessibility
- Review error messages
- Adjust retry settings

### Memory Issues
- Reduce worker count
- Process in smaller batches
- Use ThreadPoolExecutor instead of ProcessPoolExecutor

## Integration

### With Event System

```python
# Subscribe to batch events
event_bus.subscribe(EventType.CONVERSION_STARTED, handler)
event_bus.subscribe(EventType.CONVERSION_COMPLETED, handler)
event_bus.subscribe(EventType.CONVERSION_FAILED, handler)
```

### With Workspace System

Batch processing can be integrated with workspaces for organized batch operations.

## See Also

- [Batch Processor API](../core/batch_processor.py)
- [Batch UI Components](../components/batch_ui.py)
- [Batch Window](../views/batch_window.py)

