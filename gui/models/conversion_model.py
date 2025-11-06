"""
Conversion model for MarkItDown GUI.

This module contains the business logic for file conversion operations.
"""

import asyncio
from pathlib import Path
from typing import Optional, Callable, Any
import logging
import time

try:
    from markitdown import MarkItDown
except ImportError:
    MarkItDown = None
    logging.warning("MarkItDown not available. Install with: pip install markitdown[all]")

from gui.core.observer import Observable
from gui.core.events import Event, EventType, EventBus
from gui.core.state import ConversionState, ConversionStatus

logger = logging.getLogger(__name__)


class ConversionModel(Observable):
    """
    Model for handling file conversion operations.
    
    This class encapsulates the business logic for converting files
    to Markdown using the MarkItDown library.
    """

    def __init__(
        self,
        event_bus: Optional[EventBus] = None,
        enable_plugins: bool = False,
        docintel_endpoint: Optional[str] = None,
        llm_client: Optional[Any] = None,
        llm_model: Optional[str] = None
    ) -> None:
        """
        Initialize the conversion model.
        
        Args:
            event_bus: Optional event bus for emitting events
            enable_plugins: Whether to enable MarkItDown plugins
            docintel_endpoint: Optional Azure Document Intelligence endpoint
            llm_client: Optional LLM client for image descriptions
            llm_model: Optional LLM model name
        """
        super().__init__()
        self.event_bus = event_bus
        self._markitdown: Optional[MarkItDown] = None
        self._current_task: Optional[asyncio.Task] = None
        self._cancelled = False

        # Initialize MarkItDown
        try:
            if MarkItDown is None:
                raise ImportError("MarkItDown is not installed")
            
            self._markitdown = MarkItDown(
                enable_plugins=enable_plugins,
                docintel_endpoint=docintel_endpoint,
                llm_client=llm_client,
                llm_model=llm_model
            )
            logger.info("MarkItDown initialized successfully")
        except Exception as e:
            logger.error(f"Failed to initialize MarkItDown: {e}", exc_info=True)
            raise

    def update_settings(
        self,
        enable_plugins: Optional[bool] = None,
        docintel_endpoint: Optional[str] = None,
        llm_client: Optional[Any] = None,
        llm_model: Optional[str] = None
    ) -> None:
        """
        Update conversion settings.
        
        Args:
            enable_plugins: Whether to enable plugins
            docintel_endpoint: Document Intelligence endpoint
            llm_client: LLM client
            llm_model: LLM model name
        """
        # Reinitialize MarkItDown with new settings
        try:
            self._markitdown = MarkItDown(
                enable_plugins=enable_plugins if enable_plugins is not None else False,
                docintel_endpoint=docintel_endpoint,
                llm_client=llm_client,
                llm_model=llm_model
            )
            logger.info("MarkItDown settings updated")
        except Exception as e:
            logger.error(f"Failed to update MarkItDown settings: {e}", exc_info=True)
            raise

    async def convert_async(
        self,
        input_file: Path,
        output_file: Optional[Path] = None,
        progress_callback: Optional[Callable[[float], None]] = None
    ) -> ConversionState:
        """
        Convert a file to Markdown asynchronously.
        
        Args:
            input_file: Path to the input file
            output_file: Optional path for output file
            progress_callback: Optional callback for progress updates
                              Signature: callback(progress: float) -> None
                              progress is between 0.0 and 1.0
        
        Returns:
            ConversionState with the result
        
        Raises:
            ValueError: If input file doesn't exist
            RuntimeError: If conversion fails
        """
        if not input_file.exists():
            raise ValueError(f"Input file does not exist: {input_file}")

        if self._current_task and not self._current_task.done():
            raise RuntimeError("A conversion is already in progress")

        self._cancelled = False
        conversion_state = ConversionState(
            input_file=input_file,
            output_file=output_file,
            status=ConversionStatus.IN_PROGRESS,
            start_time=time.time()
        )

        # Emit start event
        if self.event_bus:
            self.event_bus.emit(Event(
                EventType.CONVERSION_STARTED,
                {"input_file": str(input_file), "output_file": str(output_file) if output_file else None},
                source="ConversionModel"
            ))

        self.notify(conversion_state)

        try:
            # Run conversion in executor to avoid blocking
            loop = asyncio.get_event_loop()
            
            def run_conversion() -> str:
                """Run the actual conversion in a thread."""
                if self._cancelled:
                    raise asyncio.CancelledError("Conversion cancelled")
                
                if progress_callback:
                    progress_callback(0.1)
                
                if self._markitdown is None:
                    raise RuntimeError("MarkItDown is not initialized")
                
                result = self._markitdown.convert(str(input_file))
                
                if progress_callback:
                    progress_callback(0.9)
                
                if self._cancelled:
                    raise asyncio.CancelledError("Conversion cancelled")
                
                return result.text_content

            # Execute conversion
            result_text = await loop.run_in_executor(None, run_conversion)

            if self._cancelled:
                conversion_state.status = ConversionStatus.CANCELLED
                conversion_state.end_time = time.time()
                
                if self.event_bus:
                    self.event_bus.emit(Event(
                        EventType.CONVERSION_CANCELLED,
                        {"input_file": str(input_file)},
                        source="ConversionModel"
                    ))
            else:
                # Save to file if output specified
                if output_file:
                    output_file.parent.mkdir(parents=True, exist_ok=True)
                    output_file.write_text(result_text, encoding='utf-8')

                conversion_state.status = ConversionStatus.COMPLETED
                conversion_state.result_text = result_text
                conversion_state.progress = 1.0
                conversion_state.end_time = time.time()

                if self.event_bus:
                    self.event_bus.emit(Event(
                        EventType.CONVERSION_COMPLETED,
                        {
                            "input_file": str(input_file),
                            "output_file": str(output_file) if output_file else None,
                            "duration": conversion_state.duration
                        },
                        source="ConversionModel"
                    ))

                if progress_callback:
                    progress_callback(1.0)

        except asyncio.CancelledError:
            conversion_state.status = ConversionStatus.CANCELLED
            conversion_state.end_time = time.time()
            logger.info(f"Conversion cancelled: {input_file}")
        except Exception as e:
            conversion_state.status = ConversionStatus.FAILED
            conversion_state.error_message = str(e)
            conversion_state.end_time = time.time()
            logger.error(f"Conversion failed: {input_file}", exc_info=True)

            if self.event_bus:
                self.event_bus.emit(Event(
                    EventType.CONVERSION_FAILED,
                    {"input_file": str(input_file), "error": str(e)},
                    source="ConversionModel"
                ))

        self.notify(conversion_state)
        return conversion_state

    def convert(
        self,
        input_file: Path,
        output_file: Optional[Path] = None,
        progress_callback: Optional[Callable[[float], None]] = None
    ) -> ConversionState:
        """
        Convert a file to Markdown synchronously.
        
        This is a convenience method that runs the async conversion
        in a new event loop.
        
        Args:
            input_file: Path to the input file
            output_file: Optional path for output file
            progress_callback: Optional callback for progress updates
        
        Returns:
            ConversionState with the result
        """
        try:
            loop = asyncio.get_event_loop()
        except RuntimeError:
            loop = asyncio.new_event_loop()
            asyncio.set_event_loop(loop)

        self._current_task = loop.create_task(
            self.convert_async(input_file, output_file, progress_callback)
        )
        
        try:
            return loop.run_until_complete(self._current_task)
        finally:
            self._current_task = None

    def cancel(self) -> None:
        """Cancel the current conversion if in progress."""
        if self._current_task and not self._current_task.done():
            self._cancelled = True
            self._current_task.cancel()
            logger.info("Conversion cancellation requested")

    def is_converting(self) -> bool:
        """
        Check if a conversion is currently in progress.
        
        Returns:
            True if conversion is in progress
        """
        return self._current_task is not None and not self._current_task.done()

    @property
    def markitdown(self) -> Optional[MarkItDown]:
        """
        Get the underlying MarkItDown instance.
        
        Returns:
            MarkItDown instance or None if not initialized
        """
        return self._markitdown

