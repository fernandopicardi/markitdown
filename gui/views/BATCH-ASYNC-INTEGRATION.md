# Batch Processing with AsyncIO and Multiprocessing

## Overview

The batch processing system now uses **asyncio for I/O-bound operations** and **multiprocessing for CPU-bound operations**, providing optimal performance for different types of conversions.

## Architecture

### I/O-Bound Operations (AsyncIO)
- **Use Case**: File reading, network operations, disk I/O
- **Implementation**: `asyncio` with async/await
- **Benefits**: 
  - Non-blocking I/O
  - Efficient resource usage
  - High concurrency
  - Better for file operations

### CPU-Bound Operations (Multiprocessing)
- **Use Case**: CPU-intensive conversions, parsing, computation
- **Implementation**: `ProcessPoolExecutor`
- **Benefits**:
  - True parallelism
  - Bypasses GIL (Global Interpreter Lock)
  - Better for CPU-intensive tasks
  - Utilizes multiple CPU cores

## Usage

### Async I/O-Bound Processing

```python
from gui.core.batch_processor import BatchProcessor
import asyncio

async def async_convert(input_file: str, output_file: Optional[str] = None):
    """Async conversion function."""
    # Use async file operations
    # Use async network calls if needed
    result = await some_async_operation(input_file)
    return {"text_content": result}

processor = BatchProcessor(
    event_bus=event_bus,
    max_workers=8,  # More workers for I/O-bound
    use_processes=False,  # Use threads, not processes
    async_conversion_func=async_convert,  # Async function
)
```

### CPU-Bound Processing

```python
from gui.core.batch_processor import BatchProcessor

def cpu_bound_convert(input_file: str, output_file: Optional[str] = None):
    """CPU-bound conversion function."""
    # Heavy computation
    # Parsing, analysis, etc.
    result = heavy_computation(input_file)
    return {"text_content": result}

processor = BatchProcessor(
    event_bus=event_bus,
    max_workers=4,  # Match CPU cores
    use_processes=True,  # Use processes for CPU-bound
    conversion_func=cpu_bound_convert,  # Sync function
)
```

### Hybrid Approach

```python
# Use async for I/O, processes for CPU
processor = BatchProcessor(
    event_bus=event_bus,
    max_workers=4,
    use_processes=True,  # For CPU-bound parts
    async_conversion_func=async_io_operation,  # For I/O parts
)
```

## Implementation Details

### Async Event Loop

The batch processor creates a separate async event loop in a background thread:

```python
# Async loop runs in separate thread
async_loop = asyncio.new_event_loop()
asyncio.set_event_loop(async_loop)
async_loop.run_forever()
```

### Task Submission

Tasks are submitted based on operation type:

```python
if use_async:
    # Submit to async loop
    async_task = asyncio.run_coroutine_threadsafe(
        process_task_async(task),
        async_loop
    )
else:
    if use_processes:
        # CPU-bound: ProcessPoolExecutor
        future = executor.submit(process_task_cpu_bound, task)
    else:
        # I/O-bound: ThreadPoolExecutor
        future = executor.submit(process_task, task)
```

### Result Handling

Results are handled uniformly regardless of execution method:

```python
def _handle_task_result(task, result):
    """Shared result handler for sync and async."""
    if result["success"]:
        # Save result
        # Update statistics
        # Emit events
    else:
        # Retry logic
        # Error handling
```

## Performance Considerations

### I/O-Bound (AsyncIO)
- **Workers**: 8-16 (can handle many concurrent I/O operations)
- **Memory**: Lower overhead
- **Best For**: File reading, network operations
- **Example**: Reading PDFs, fetching web content

### CPU-Bound (Multiprocessing)
- **Workers**: 2-4 (match CPU cores)
- **Memory**: Higher overhead (separate processes)
- **Best For**: Parsing, computation, analysis
- **Example**: PDF parsing, image processing

### Choosing the Right Approach

```python
# I/O-bound: Many file reads
use_async = True
use_processes = False
max_workers = 8

# CPU-bound: Heavy parsing
use_async = False
use_processes = True
max_workers = 4

# Mixed: I/O + CPU
use_async = True  # For I/O parts
use_processes = True  # For CPU parts
max_workers = 4
```

## Integration with ConversionModel

The batch processor integrates with ConversionModel:

```python
# Async wrapper for ConversionModel
async def async_convert(input_file: str, output_file: Optional[str] = None):
    loop = asyncio.get_event_loop()
    result = await loop.run_in_executor(
        None,  # Use default executor
        lambda: conversion_model.convert(
            Path(input_file),
            Path(output_file) if output_file else None
        )
    )
    return {"text_content": result.result_text}
```

## Best Practices

1. **Use AsyncIO for I/O**: File operations, network calls
2. **Use Multiprocessing for CPU**: Heavy computation, parsing
3. **Match Workers to Resources**: 
   - I/O: More workers (8-16)
   - CPU: Match CPU cores (2-4)
4. **Monitor Performance**: Adjust based on actual performance
5. **Test Both Approaches**: Choose based on your use case

## Example: Full Integration

```python
from gui.views.batch_window import BatchProcessingWindow
from gui.core.events import EventBus
from gui.models.conversion_model import ConversionModel
import asyncio

event_bus = EventBus()
conversion_model = ConversionModel(event_bus=event_bus)

# Window automatically uses async for I/O-bound operations
window = BatchProcessingWindow(
    event_bus=event_bus,
    conversion_model=conversion_model,
)
window.run()
```

## Performance Metrics

### AsyncIO Benefits
- **Throughput**: 2-4x improvement for I/O-bound
- **Resource Usage**: Lower memory footprint
- **Scalability**: Handles more concurrent operations

### Multiprocessing Benefits
- **CPU Utilization**: Uses all CPU cores
- **True Parallelism**: Bypasses GIL
- **Isolation**: Process isolation prevents crashes

## Troubleshooting

### Async Loop Issues
- Ensure async loop is properly initialized
- Check for blocking operations in async functions
- Verify event loop is running

### Process Issues
- Check process count (don't exceed CPU cores)
- Monitor memory usage
- Verify process communication

### Performance Issues
- Profile to identify bottlenecks
- Adjust worker count
- Choose appropriate executor type

## See Also

- [Batch Processing README](BATCH-PROCESSING-README.md)
- [Batch System Summary](BATCH-SYSTEM-SUMMARY.md)
- [Python asyncio Documentation](https://docs.python.org/3/library/asyncio.html)
- [Python multiprocessing Documentation](https://docs.python.org/3/library/multiprocessing.html)

