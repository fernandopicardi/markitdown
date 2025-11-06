"""
State management for MarkItDown GUI.

This module provides centralized state management for the application,
following a unidirectional data flow pattern.
"""

from dataclasses import dataclass, field
from enum import Enum
from typing import Any, Dict, Optional, List, Callable
from pathlib import Path
import logging

logger = logging.getLogger(__name__)


class ConversionStatus(Enum):
    """Status of a conversion operation."""

    IDLE = "idle"
    IN_PROGRESS = "in_progress"
    COMPLETED = "completed"
    FAILED = "failed"
    CANCELLED = "cancelled"


@dataclass
class ConversionState:
    """
    State for a single conversion operation.
    
    Tracks the progress and result of converting a file to Markdown.
    """

    input_file: Optional[Path] = None
    output_file: Optional[Path] = None
    status: ConversionStatus = ConversionStatus.IDLE
    progress: float = 0.0  # 0.0 to 1.0
    error_message: Optional[str] = None
    result_text: Optional[str] = None
    start_time: Optional[float] = None
    end_time: Optional[float] = None

    def reset(self) -> None:
        """Reset the conversion state to initial values."""
        self.input_file = None
        self.output_file = None
        self.status = ConversionStatus.IDLE
        self.progress = 0.0
        self.error_message = None
        self.result_text = None
        self.start_time = None
        self.end_time = None

    @property
    def is_active(self) -> bool:
        """Check if conversion is currently active."""
        return self.status == ConversionStatus.IN_PROGRESS

    @property
    def is_complete(self) -> bool:
        """Check if conversion is complete."""
        return self.status == ConversionStatus.COMPLETED

    @property
    def has_error(self) -> bool:
        """Check if conversion has an error."""
        return self.status == ConversionStatus.FAILED

    @property
    def duration(self) -> Optional[float]:
        """Get conversion duration in seconds."""
        if self.start_time and self.end_time:
            return self.end_time - self.start_time
        return None


@dataclass
class AppState:
    """
    Central application state.
    
    This is the single source of truth for application state.
    All state changes should go through the StateManager.
    """

    # Conversion state
    current_conversion: ConversionState = field(default_factory=ConversionState)
    conversion_history: List[ConversionState] = field(default_factory=list)

    # File management
    recent_files: List[Path] = field(default_factory=list)
    max_recent_files: int = 10

    # Settings
    settings: Dict[str, Any] = field(default_factory=dict)
    enable_plugins: bool = False
    docintel_endpoint: Optional[str] = None
    llm_client: Optional[Any] = None
    llm_model: Optional[str] = None

    # UI state
    window_geometry: Optional[str] = None
    theme: str = "default"
    language: str = "en"

    def add_recent_file(self, file_path: Path) -> None:
        """
        Add a file to recent files list.
        
        Args:
            file_path: Path to the file to add
        """
        # Remove if already exists
        if file_path in self.recent_files:
            self.recent_files.remove(file_path)
        # Add to front
        self.recent_files.insert(0, file_path)
        # Limit size
        if len(self.recent_files) > self.max_recent_files:
            self.recent_files = self.recent_files[:self.max_recent_files]

    def get_setting(self, key: str, default: Any = None) -> Any:
        """
        Get a setting value.
        
        Args:
            key: Setting key
            default: Default value if key doesn't exist
            
        Returns:
            Setting value or default
        """
        return self.settings.get(key, default)

    def set_setting(self, key: str, value: Any) -> None:
        """
        Set a setting value.
        
        Args:
            key: Setting key
            value: Setting value
        """
        self.settings[key] = value


class StateManager:
    """
    Manages application state with change notifications.
    
    Implements the Observable pattern to notify observers of state changes.
    """

    def __init__(self, initial_state: Optional[AppState] = None) -> None:
        """
        Initialize the state manager.
        
        Args:
            initial_state: Optional initial state (creates new if None)
        """
        from gui.core.observer import Observable
        self._state = initial_state or AppState()
        self._observable = Observable()
        self._history: List[AppState] = []
        self._max_history: int = 50

    @property
    def state(self) -> AppState:
        """
        Get the current application state.
        
        Returns:
            Current application state (read-only access)
        """
        return self._state

    def update_state(self, updater: Callable[[AppState], None]) -> None:
        """
        Update state using an updater function.
        
        This is the only way to modify state, ensuring all changes
        are tracked and observers are notified.
        
        Args:
            updater: Function that modifies the state
        """
        # Save to history
        import copy
        self._history.append(copy.deepcopy(self._state))
        if len(self._history) > self._max_history:
            self._history.pop(0)

        # Update state
        updater(self._state)

        # Notify observers
        self._observable.notify(self._state)

        logger.debug("State updated")

    def set_conversion_state(self, conversion: ConversionState) -> None:
        """
        Update the current conversion state.
        
        Args:
            conversion: New conversion state
        """
        def updater(state: AppState) -> None:
            state.current_conversion = conversion

        self.update_state(updater)

    def add_conversion_to_history(self, conversion: ConversionState) -> None:
        """
        Add a completed conversion to history.
        
        Args:
            conversion: The conversion to add
        """
        def updater(state: AppState) -> None:
            state.conversion_history.append(conversion)
            # Limit history size
            if len(state.conversion_history) > 100:
                state.conversion_history = state.conversion_history[-100:]

        self.update_state(updater)

    def reset_conversion(self) -> None:
        """Reset the current conversion state."""
        def updater(state: AppState) -> None:
            state.current_conversion.reset()

        self.update_state(updater)

    def attach_observer(self, observer: Any) -> None:
        """
        Attach an observer to state changes.
        
        Args:
            observer: Observer object or callback function
        """
        if callable(observer) and not hasattr(observer, 'update'):
            # It's a callback function
            self._observable.attach_callback(observer)
        else:
            # It's an Observer object
            self._observable.attach(observer)

    def detach_observer(self, observer: Any) -> None:
        """
        Detach an observer from state changes.
        
        Args:
            observer: Observer object or callback function
        """
        if callable(observer) and not hasattr(observer, 'update'):
            self._observable.detach_callback(observer)
        else:
            self._observable.detach(observer)

    def undo(self) -> bool:
        """
        Undo the last state change.
        
        Returns:
            True if undo was successful, False if no history
        """
        if not self._history:
            return False

        self._state = self._history.pop()
        self._observable.notify(self._state)
        logger.debug("State undone")
        return True

    def can_undo(self) -> bool:
        """
        Check if undo is possible.
        
        Returns:
            True if there is history to undo
        """
        return len(self._history) > 0

    def get_state_snapshot(self) -> AppState:
        """
        Get a deep copy of the current state.
        
        Returns:
            Deep copy of current state
        """
        import copy
        return copy.deepcopy(self._state)

