"""
Tests for the Observer pattern implementation.
"""

import pytest
from gui.core.observer import Observer, Observable, EventObserver


class TestObserver(Observer):
    """Test observer implementation."""

    def __init__(self) -> None:
        """Initialize test observer."""
        self.update_count = 0
        self.last_subject = None
        self.last_event = None

    def update(self, subject: Observable, event=None) -> None:
        """
        Update method for testing.
        
        Args:
            subject: The observable subject
            event: Optional event data
        """
        self.update_count += 1
        self.last_subject = subject
        self.last_event = event


class TestObservable(Observable):
    """Test observable implementation."""

    def __init__(self) -> None:
        """Initialize test observable."""
        super().__init__()
        self.value = 0

    def increment(self) -> None:
        """Increment value and notify observers."""
        self.value += 1
        self.notify({"action": "increment", "value": self.value})


def test_observer_attach_detach() -> None:
    """Test attaching and detaching observers."""
    observable = TestObservable()
    observer = TestObserver()

    # Attach observer
    observable.attach(observer)
    assert observable.observer_count == 1

    # Notify
    observable.increment()
    assert observer.update_count == 1
    assert observer.last_subject == observable

    # Detach observer
    observable.detach(observer)
    assert observable.observer_count == 0

    # Notify again (should not update observer)
    observable.increment()
    assert observer.update_count == 1  # Still 1, not 2


def test_observer_callback() -> None:
    """Test callback-based observers."""
    observable = TestObservable()
    callback_calls = []

    def callback(subject: Observable, event=None) -> None:
        """Test callback."""
        callback_calls.append((subject, event))

    # Attach callback
    observable.attach_callback(callback)
    assert observable.observer_count == 1

    # Notify
    observable.increment()
    assert len(callback_calls) == 1

    # Detach callback
    observable.detach_callback(callback)
    assert observable.observer_count == 0


def test_observer_multiple() -> None:
    """Test multiple observers."""
    observable = TestObservable()
    observer1 = TestObserver()
    observer2 = TestObserver()

    observable.attach(observer1)
    observable.attach(observer2)
    assert observable.observer_count == 2

    observable.increment()
    assert observer1.update_count == 1
    assert observer2.update_count == 1


def test_observer_clear() -> None:
    """Test clearing all observers."""
    observable = TestObservable()
    observer1 = TestObserver()
    observer2 = TestObserver()

    observable.attach(observer1)
    observable.attach(observer2)
    assert observable.observer_count == 2

    observable.clear_observers()
    assert observable.observer_count == 0

    observable.increment()
    assert observer1.update_count == 0
    assert observer2.update_count == 0


def test_observer_duplicate_attach() -> None:
    """Test that duplicate attachment raises error."""
    observable = TestObservable()
    observer = TestObserver()

    observable.attach(observer)
    with pytest.raises(ValueError, match="already attached"):
        observable.attach(observer)


def test_event_observer() -> None:
    """Test EventObserver integration."""
    from gui.core.events import EventBus, Event, EventType

    event_bus = EventBus()
    events_received = []

    def event_handler(event: Event) -> None:
        """Event handler for testing."""
        events_received.append(event)

    event_bus.subscribe(EventType.STATE_CHANGED, event_handler)

    observable = TestObservable()
    event_observer = EventObserver(event_bus, EventType.STATE_CHANGED)

    observable.attach(event_observer)
    observable.increment()

    assert len(events_received) == 1
    assert events_received[0].event_type == EventType.STATE_CHANGED

