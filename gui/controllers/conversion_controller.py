"""
Conversion controller for MarkItDown GUI.

This module contains the controller that coordinates between the
conversion model and the main window view.
"""

import asyncio
from pathlib import Path
from typing import Optional
import logging

from gui.core.observer import Observer
from gui.core.events import Event, EventType, EventBus
from gui.core.state import StateManager, AppState, ConversionState
from gui.models.conversion_model import ConversionModel
from gui.views.main_window import MainWindow

logger = logging.getLogger(__name__)


class ConversionController(Observer):
    """
    Controller for conversion operations.
    
    This class implements the controller layer of the MVC pattern,
    coordinating between the model (ConversionModel) and view (MainWindow).
    It handles user actions and updates both model and view accordingly.
    """

    def __init__(
        self,
        model: ConversionModel,
        view: MainWindow,
        state_manager: StateManager,
        event_bus: EventBus
    ) -> None:
        """
        Initialize the conversion controller.
        
        Args:
            model: The conversion model
            view: The main window view
            state_manager: The state manager
            event_bus: The event bus
        """
        super().__init__()
        self.model = model
        self.view = view
        self.state_manager = state_manager
        self.event_bus = event_bus
        self._conversion_task: Optional[asyncio.Task] = None

        # Attach to state manager
        self.state_manager.attach_observer(self)

        # Set up event listeners
        self._setup_event_listeners()

        logger.info("ConversionController initialized")

    def _setup_event_listeners(self) -> None:
        """Set up event bus listeners."""
        self.event_bus.subscribe(EventType.FILE_SELECTED, self._on_file_selected)
        self.event_bus.subscribe(EventType.CONVERSION_CANCELLED, self._on_cancel_requested)

    def _on_file_selected(self, event: Event) -> None:
        """
        Handle file selection event.
        
        Args:
            event: File selection event
        """
        input_file_str = event.get("input_file")
        output_file_str = event.get("output_file")

        if not input_file_str:
            self.event_bus.emit(Event(
                EventType.UI_ERROR,
                {"message": "No input file specified"},
                source="ConversionController"
            ))
            return

        input_file = Path(input_file_str)
        output_file = Path(output_file_str) if output_file_str else None

        # Start conversion
        self.start_conversion(input_file, output_file)

    def _on_cancel_requested(self, event: Event) -> None:
        """
        Handle cancel request event.
        
        Args:
            event: Cancel event
        """
        if event.source == "MainWindow":
            self.cancel_conversion()

    def start_conversion(
        self,
        input_file: Path,
        output_file: Optional[Path] = None
    ) -> None:
        """
        Start a conversion operation.
        
        Args:
            input_file: Path to input file
            output_file: Optional path to output file
        """
        if self.model.is_converting():
            self.event_bus.emit(Event(
                EventType.UI_WARNING,
                {"message": "A conversion is already in progress"},
                source="ConversionController"
            ))
            return

        # Update state
        conversion_state = ConversionState(
            input_file=input_file,
            output_file=output_file
        )
        self.state_manager.set_conversion_state(conversion_state)

        # Start async conversion
        loop = asyncio.get_event_loop()
        self._conversion_task = loop.create_task(
            self._run_conversion_async(input_file, output_file)
        )

        logger.info(f"Conversion started: {input_file} -> {output_file}")

    async def _run_conversion_async(
        self,
        input_file: Path,
        output_file: Optional[Path]
    ) -> None:
        """
        Run conversion asynchronously with progress updates.
        
        Args:
            input_file: Path to input file
            output_file: Optional path to output file
        """
        def progress_callback(progress: float) -> None:
            """Progress callback for conversion."""
            # Update state
            def updater(state: AppState) -> None:
                state.current_conversion.progress = progress

            self.state_manager.update_state(updater)

            # Emit progress event
            self.event_bus.emit(Event(
                EventType.CONVERSION_PROGRESS,
                {"progress": progress},
                source="ConversionController"
            ))

        try:
            # Run conversion
            conversion_state = await self.model.convert_async(
                input_file,
                output_file,
                progress_callback
            )

            # Update state with result
            self.state_manager.set_conversion_state(conversion_state)

            # Add to history if successful
            if conversion_state.is_complete:
                self.state_manager.add_conversion_to_history(conversion_state)

                # Add to recent files
                def updater(state: AppState) -> None:
                    state.add_recent_file(input_file)

                self.state_manager.update_state(updater)

        except Exception as e:
            logger.error(f"Conversion error: {e}", exc_info=True)
            self.event_bus.emit(Event(
                EventType.CONVERSION_FAILED,
                {"error": str(e)},
                source="ConversionController"
            ))

            # Update state with error
            from gui.core.state import ConversionStatus
            def updater(state: AppState) -> None:
                state.current_conversion.status = ConversionStatus.FAILED
                state.current_conversion.error_message = str(e)

            self.state_manager.update_state(updater)
        finally:
            self._conversion_task = None

    def cancel_conversion(self) -> None:
        """Cancel the current conversion if in progress."""
        if self.model.is_converting():
            self.model.cancel()
            logger.info("Conversion cancellation requested")

            # Update state
            from gui.core.state import ConversionStatus
            def updater(state: AppState) -> None:
                state.current_conversion.status = ConversionStatus.CANCELLED

            self.state_manager.update_state(updater)

    def update(self, subject: Any, event: Optional[Any] = None) -> None:
        """
        Update method from Observer pattern.
        
        Called when the observed subject (StateManager) notifies of changes.
        
        Args:
            subject: The observable subject
            event: Optional event data (AppState)
        """
        if isinstance(event, AppState):
            # State has changed, view will be updated automatically
            # through its own observer connection
            pass

    def update_model_settings(
        self,
        enable_plugins: Optional[bool] = None,
        docintel_endpoint: Optional[str] = None,
        llm_client: Optional[Any] = None,
        llm_model: Optional[str] = None
    ) -> None:
        """
        Update model settings.
        
        Args:
            enable_plugins: Whether to enable plugins
            docintel_endpoint: Document Intelligence endpoint
            llm_client: LLM client
            llm_model: LLM model name
        """
        try:
            self.model.update_settings(
                enable_plugins=enable_plugins,
                docintel_endpoint=docintel_endpoint,
                llm_client=llm_client,
                llm_model=llm_model
            )

            # Update state
            def updater(state: AppState) -> None:
                if enable_plugins is not None:
                    state.enable_plugins = enable_plugins
                if docintel_endpoint is not None:
                    state.docintel_endpoint = docintel_endpoint
                if llm_model is not None:
                    state.llm_model = llm_model

            self.state_manager.update_state(updater)

            logger.info("Model settings updated")
        except Exception as e:
            logger.error(f"Failed to update model settings: {e}", exc_info=True)
            self.event_bus.emit(Event(
                EventType.UI_ERROR,
                {"message": f"Failed to update settings: {e}"},
                source="ConversionController"
            ))

