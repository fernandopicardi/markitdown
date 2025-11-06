"""
Event system for MarkItDown GUI.

This module provides a custom event system for decoupled communication
between components using an event bus pattern.
"""

from enum import Enum
from dataclasses import dataclass, field
from typing import Any, Dict, List, Callable, Optional
from collections import defaultdict
import logging
from datetime import datetime

logger = logging.getLogger(__name__)


class EventType(Enum):
    """
    Enumeration of all event types in the application.
    
    This centralizes event type definitions for type safety and discoverability.
    """

    # Conversion events
    CONVERSION_STARTED = "conversion.started"
    CONVERSION_PROGRESS = "conversion.progress"
    CONVERSION_COMPLETED = "conversion.completed"
    CONVERSION_FAILED = "conversion.failed"
    CONVERSION_CANCELLED = "conversion.cancelled"

    # File events
    FILE_SELECTED = "file.selected"
    FILE_LOADED = "file.loaded"
    FILE_SAVED = "file.saved"
    FILE_ERROR = "file.error"

    # State events
    STATE_CHANGED = "state.changed"
    SETTINGS_CHANGED = "settings.changed"

    # UI events
    UI_READY = "ui.ready"
    UI_ERROR = "ui.error"
    UI_WARNING = "ui.warning"
    UI_INFO = "ui.info"

    # Application events
    APP_STARTED = "app.started"
    APP_SHUTDOWN = "app.shutdown"
    APP_ERROR = "app.error"


@dataclass
class Event:
    """
    Represents an event in the application.
    
    Events are immutable data structures that carry information about
    something that happened in the application.
    """

    event_type: EventType
    data: Dict[str, Any] = field(default_factory=dict)
    timestamp: datetime = field(default_factory=datetime.now)
    source: Optional[str] = None

    def __post_init__(self) -> None:
        """Validate event after initialization."""
        if not isinstance(self.event_type, EventType):
            raise TypeError(f"event_type must be EventType, got {type(self.event_type)}")

    def __str__(self) -> str:
        """String representation of the event."""
        return f"Event({self.event_type.value}, source={self.source}, data={len(self.data)} items)"

    def get(self, key: str, default: Any = None) -> Any:
        """
        Get a value from the event data.
        
        Args:
            key: The key to retrieve
            default: Default value if key doesn't exist
            
        Returns:
            The value associated with the key, or default
        """
        return self.data.get(key, default)

    def has(self, key: str) -> bool:
        """
        Check if the event data contains a key.
        
        Args:
            key: The key to check
            
        Returns:
            True if key exists, False otherwise
        """
        return key in self.data


class EventBus:
    """
    Central event bus for the application.
    
    Implements the publish-subscribe pattern for decoupled communication.
    Components can subscribe to events and emit events without knowing
    about each other.
    """

    def __init__(self) -> None:
        """Initialize the event bus with empty subscribers."""
        self._subscribers: Dict[EventType, List[Callable[[Event], None]]] = defaultdict(list)
        self._global_subscribers: List[Callable[[Event], None]] = []
        self._event_history: List[Event] = []
        self._max_history: int = 1000
        self._enabled: bool = True

    def subscribe(
        self,
        event_type: EventType,
        callback: Callable[[Event], None],
        global_subscriber: bool = False
    ) -> None:
        """
        Subscribe to events of a specific type.
        
        Args:
            event_type: The type of event to subscribe to
            callback: Function to call when event is emitted
                     Signature: callback(event: Event) -> None
            global_subscriber: If True, subscribe to all events
            
        Raises:
            ValueError: If callback is already subscribed
        """
        if global_subscriber:
            if callback in self._global_subscribers:
                raise ValueError("Callback is already a global subscriber")
            self._global_subscribers.append(callback)
            logger.debug(f"Global subscriber added: {callback.__name__}")
        else:
            if callback in self._subscribers[event_type]:
                raise ValueError(f"Callback already subscribed to {event_type.value}")
            self._subscribers[event_type].append(callback)
            logger.debug(f"Subscriber added for {event_type.value}: {callback.__name__}")

    def unsubscribe(
        self,
        event_type: Optional[EventType],
        callback: Callable[[Event], None]
    ) -> None:
        """
        Unsubscribe from events.
        
        Args:
            event_type: The event type to unsubscribe from (None for global)
            callback: The callback to remove
        """
        if event_type is None:
            if callback in self._global_subscribers:
                self._global_subscribers.remove(callback)
                logger.debug(f"Global subscriber removed: {callback.__name__}")
        else:
            if callback in self._subscribers[event_type]:
                self._subscribers[event_type].remove(callback)
                logger.debug(f"Subscriber removed from {event_type.value}: {callback.__name__}")

    def emit(self, event: Event) -> None:
        """
        Emit an event to all subscribers.
        
        Args:
            event: The event to emit
        """
        if not self._enabled:
            return

        # Add to history
        self._event_history.append(event)
        if len(self._event_history) > self._max_history:
            self._event_history.pop(0)

        # Notify specific subscribers
        subscribers = self._subscribers.get(event.event_type, [])
        for callback in subscribers:
            try:
                callback(event)
            except Exception as e:
                logger.error(
                    f"Error in event subscriber for {event.event_type.value}: {e}",
                    exc_info=True
                )

        # Notify global subscribers
        for callback in self._global_subscribers:
            try:
                callback(event)
            except Exception as e:
                logger.error(f"Error in global event subscriber: {e}", exc_info=True)

        logger.debug(f"Event emitted: {event}")

    def clear_subscribers(self, event_type: Optional[EventType] = None) -> None:
        """
        Clear all subscribers for an event type or all subscribers.
        
        Args:
            event_type: The event type to clear (None for all)
        """
        if event_type is None:
            self._subscribers.clear()
            self._global_subscribers.clear()
            logger.debug("All subscribers cleared")
        else:
            self._subscribers[event_type] = []
            logger.debug(f"Subscribers cleared for {event_type.value}")

    def get_history(self, event_type: Optional[EventType] = None, limit: int = 100) -> List[Event]:
        """
        Get event history.
        
        Args:
            event_type: Filter by event type (None for all)
            limit: Maximum number of events to return
            
        Returns:
            List of recent events
        """
        events = self._event_history
        if event_type is not None:
            events = [e for e in events if e.event_type == event_type]
        return events[-limit:]

    def clear_history(self) -> None:
        """Clear the event history."""
        self._event_history.clear()
        logger.debug("Event history cleared")

    def enable(self) -> None:
        """Enable event bus (events will be processed)."""
        self._enabled = True
        logger.debug("Event bus enabled")

    def disable(self) -> None:
        """Disable event bus (events will be ignored)."""
        self._enabled = False
        logger.debug("Event bus disabled")

    @property
    def is_enabled(self) -> bool:
        """Check if event bus is enabled."""
        return self._enabled

    @property
    def subscriber_count(self) -> int:
        """Get total number of subscribers."""
        return sum(len(callbacks) for callbacks in self._subscribers.values()) + len(
            self._global_subscribers
        )

