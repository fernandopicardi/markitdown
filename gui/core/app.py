"""
Main application class for MarkItDown GUI.

This module contains the application entry point and initialization logic.
"""

import sys
import logging
from pathlib import Path
from typing import Optional, Any
import asyncio

from gui.core.events import EventBus, EventType
from gui.core.state import StateManager, AppState
from gui.models.conversion_model import ConversionModel
from gui.views.main_window import MainWindow
from gui.views.modern_window import ModernMainWindow
from gui.controllers.conversion_controller import ConversionController

logger = logging.getLogger(__name__)


class MarkItDownApp:
    """
    Main application class.
    
    This class initializes and coordinates all components of the application
    following the MVC/MVP pattern.
    """

    def __init__(
        self,
        enable_plugins: bool = False,
        docintel_endpoint: Optional[str] = None,
        llm_client: Optional[Any] = None,
        llm_model: Optional[str] = None
    ) -> None:
        """
        Initialize the application.
        
        Args:
            enable_plugins: Whether to enable MarkItDown plugins
            docintel_endpoint: Optional Azure Document Intelligence endpoint
            llm_client: Optional LLM client for image descriptions
            llm_model: Optional LLM model name
        """
        self._setup_logging()

        # Initialize core components
        self.event_bus = EventBus()
        self.state_manager = StateManager()
        self.model = ConversionModel(
            event_bus=self.event_bus,
            enable_plugins=enable_plugins,
            docintel_endpoint=docintel_endpoint,
            llm_client=llm_client,
            llm_model=llm_model
        )

        # Initialize view (use ModernMainWindow for CustomTkinter)
        try:
            self.view = ModernMainWindow(
                event_bus=self.event_bus,
                state_update_callback=self._on_state_update
            )
        except ImportError:
            logger.warning("CustomTkinter not available, falling back to standard Tkinter")
            self.view = MainWindow(
                event_bus=self.event_bus,
                state_update_callback=self._on_state_update
            )

        # Initialize controller
        self.controller = ConversionController(
            model=self.model,
            view=self.view,
            state_manager=self.state_manager,
            event_bus=self.event_bus
        )

        # Connect view to state manager
        self.state_manager.attach_observer(self.view)

        # Set up global event handlers
        self._setup_global_handlers()

        logger.info("MarkItDownApp initialized")

    def _setup_logging(self) -> None:
        """Configure application logging."""
        logging.basicConfig(
            level=logging.INFO,
            format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
            handlers=[
                logging.StreamHandler(sys.stdout),
                logging.FileHandler('markitdown-gui.log')
            ]
        )

    def _setup_global_handlers(self) -> None:
        """Set up global event handlers."""
        self.event_bus.subscribe(EventType.APP_ERROR, self._on_app_error)
        self.event_bus.subscribe(EventType.APP_SHUTDOWN, self._on_app_shutdown)

    def _on_state_update(self, state: AppState) -> None:
        """
        Handle state updates.
        
        Args:
            state: Updated application state
        """
        # This callback can be used for additional state-based logic
        pass

    def _on_app_error(self, event: Any) -> None:
        """
        Handle application errors.
        
        Args:
            event: Error event
        """
        error = event.get("error", "Unknown error") if hasattr(event, 'get') else str(event)
        logger.error(f"Application error: {error}")

    def _on_app_shutdown(self, event: Any) -> None:
        """
        Handle application shutdown.
        
        Args:
            event: Shutdown event
        """
        logger.info("Application shutdown requested")
        self.shutdown()

    def run(self) -> None:
        """Start the application."""
        logger.info("Starting MarkItDown GUI application")

        # Emit app started event
        from gui.core.events import Event
        self.event_bus.emit(Event(
            EventType.APP_STARTED,
            {},
            source="MarkItDownApp"
        ))

        # Start the UI event loop
        try:
            self.view.run()
        except KeyboardInterrupt:
            logger.info("Application interrupted by user")
        except Exception as e:
            logger.error(f"Application error: {e}", exc_info=True)
            self.event_bus.emit(Event(
                EventType.APP_ERROR,
                {"error": str(e)},
                source="MarkItDownApp"
            ))
        finally:
            self.shutdown()

    def shutdown(self) -> None:
        """Shutdown the application gracefully."""
        logger.info("Shutting down application")

        # Cancel any ongoing conversions
        if self.model.is_converting():
            self.model.cancel()

        # Emit shutdown event
        from gui.core.events import Event
        self.event_bus.emit(Event(
            EventType.APP_SHUTDOWN,
            {},
            source="MarkItDownApp"
        ))

        # Clean up
        self.event_bus.clear_subscribers()
        self.state_manager.detach_observer(self.view)
        self.state_manager.detach_observer(self.controller)

        logger.info("Application shutdown complete")


def create_app(
    enable_plugins: bool = False,
    docintel_endpoint: Optional[str] = None,
    llm_client: Optional[Any] = None,
    llm_model: Optional[str] = None
) -> MarkItDownApp:
    """
    Factory function to create and configure the application.
    
    Args:
        enable_plugins: Whether to enable MarkItDown plugins
        docintel_endpoint: Optional Azure Document Intelligence endpoint
        llm_client: Optional LLM client for image descriptions
        llm_model: Optional LLM model name
    
    Returns:
        Configured MarkItDownApp instance
    """
    return MarkItDownApp(
        enable_plugins=enable_plugins,
        docintel_endpoint=docintel_endpoint,
        llm_client=llm_client,
        llm_model=llm_model
    )

