"""
Observer pattern implementation for MarkItDown GUI.

This module provides a generic observer pattern implementation for
decoupled communication between components.
"""

from abc import ABC, abstractmethod
from typing import Any, List, Callable, Optional
from collections import defaultdict
import logging

logger = logging.getLogger(__name__)


class Observer(ABC):
    """
    Abstract base class for observers in the Observer pattern.
    
    Observers are notified when the subject they observe changes state.
    """

    @abstractmethod
    def update(self, subject: "Observable", event: Optional[Any] = None) -> None:
        """
        Called when the observed subject notifies of a change.
        
        Args:
            subject: The observable object that triggered the notification
            event: Optional event data associated with the notification
        """
        pass


class Observable:
    """
    Base class for observable objects in the Observer pattern.
    
    Allows objects to notify observers when their state changes.
    """

    def __init__(self) -> None:
        """Initialize the observable with an empty list of observers."""
        self._observers: List[Observer] = []
        self._observer_callbacks: List[Callable[[Any, Optional[Any]], None]] = []

    def attach(self, observer: Observer) -> None:
        """
        Attach an observer to this observable.
        
        Args:
            observer: The observer to attach
            
        Raises:
            ValueError: If observer is already attached
        """
        if observer in self._observers:
            raise ValueError("Observer is already attached")
        self._observers.append(observer)
        logger.debug(f"Observer {type(observer).__name__} attached to {type(self).__name__}")

    def detach(self, observer: Observer) -> None:
        """
        Detach an observer from this observable.
        
        Args:
            observer: The observer to detach
        """
        if observer in self._observers:
            self._observers.remove(observer)
            logger.debug(f"Observer {type(observer).__name__} detached from {type(self).__name__}")

    def attach_callback(self, callback: Callable[[Any, Optional[Any]], None]) -> None:
        """
        Attach a callback function as an observer.
        
        Args:
            callback: Function to call when notified
                     Signature: callback(subject, event) -> None
        """
        if callback not in self._observer_callbacks:
            self._observer_callbacks.append(callback)
            logger.debug(f"Callback attached to {type(self).__name__}")

    def detach_callback(self, callback: Callable[[Any, Optional[Any]], None]) -> None:
        """
        Detach a callback function observer.
        
        Args:
            callback: The callback function to detach
        """
        if callback in self._observer_callbacks:
            self._observer_callbacks.remove(callback)
            logger.debug(f"Callback detached from {type(self).__name__}")

    def notify(self, event: Optional[Any] = None) -> None:
        """
        Notify all attached observers of a state change.
        
        Args:
            event: Optional event data to pass to observers
        """
        for observer in self._observers:
            try:
                observer.update(self, event)
            except Exception as e:
                logger.error(f"Error notifying observer {type(observer).__name__}: {e}", exc_info=True)

        for callback in self._observer_callbacks:
            try:
                callback(self, event)
            except Exception as e:
                logger.error(f"Error in observer callback: {e}", exc_info=True)

    def clear_observers(self) -> None:
        """Remove all observers and callbacks."""
        self._observers.clear()
        self._observer_callbacks.clear()
        logger.debug(f"All observers cleared from {type(self).__name__}")

    @property
    def observer_count(self) -> int:
        """Get the number of attached observers."""
        return len(self._observers) + len(self._observer_callbacks)


class EventObserver(Observer):
    """
    Observer that forwards notifications to an event bus.
    
    This allows integration between the Observer pattern and the Event system.
    """

    def __init__(self, event_bus: "EventBus", event_type: "EventType") -> None:
        """
        Initialize the event observer.
        
        Args:
            event_bus: The event bus to forward events to
            event_type: The type of event to emit
        """
        self.event_bus = event_bus
        self.event_type = event_type

    def update(self, subject: Observable, event: Optional[Any] = None) -> None:
        """
        Forward the notification to the event bus.
        
        Args:
            subject: The observable that triggered the notification
            event: Optional event data
        """
        from gui.core.events import Event
        event_data = event if event is not None else {"subject": str(subject)}
        self.event_bus.emit(Event(self.event_type, event_data))

