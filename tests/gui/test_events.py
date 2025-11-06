"""
Tests for the event system.
"""

import pytest
from gui.core.events import Event, EventType, EventBus


def test_event_creation() -> None:
    """Test event creation."""
    event = Event(EventType.CONVERSION_STARTED, {"file": "test.pdf"})
    assert event.event_type == EventType.CONVERSION_STARTED
    assert event.get("file") == "test.pdf"
    assert event.has("file")
    assert not event.has("nonexistent")


def test_event_invalid_type() -> None:
    """Test that invalid event type raises error."""
    with pytest.raises(TypeError):
        Event("invalid_type", {})  # type: ignore


def test_event_bus_subscribe_emit() -> None:
    """Test subscribing to and emitting events."""
    event_bus = EventBus()
    events_received = []

    def handler(event: Event) -> None:
        """Event handler."""
        events_received.append(event)

    # Subscribe
    event_bus.subscribe(EventType.CONVERSION_STARTED, handler)
    assert event_bus.subscriber_count == 1

    # Emit
    event = Event(EventType.CONVERSION_STARTED, {"test": "data"})
    event_bus.emit(event)

    assert len(events_received) == 1
    assert events_received[0] == event


def test_event_bus_multiple_subscribers() -> None:
    """Test multiple subscribers for same event type."""
    event_bus = EventBus()
    calls1 = []
    calls2 = []

    def handler1(event: Event) -> None:
        """First handler."""
        calls1.append(event)

    def handler2(event: Event) -> None:
        """Second handler."""
        calls2.append(event)

    event_bus.subscribe(EventType.CONVERSION_STARTED, handler1)
    event_bus.subscribe(EventType.CONVERSION_STARTED, handler2)

    event = Event(EventType.CONVERSION_STARTED, {})
    event_bus.emit(event)

    assert len(calls1) == 1
    assert len(calls2) == 1


def test_event_bus_global_subscriber() -> None:
    """Test global subscribers."""
    event_bus = EventBus()
    all_events = []

    def global_handler(event: Event) -> None:
        """Global event handler."""
        all_events.append(event)

    event_bus.subscribe(EventType.CONVERSION_STARTED, global_handler, global_subscriber=True)

    event1 = Event(EventType.CONVERSION_STARTED, {})
    event2 = Event(EventType.CONVERSION_COMPLETED, {})

    event_bus.emit(event1)
    event_bus.emit(event2)

    assert len(all_events) == 2


def test_event_bus_unsubscribe() -> None:
    """Test unsubscribing from events."""
    event_bus = EventBus()
    events_received = []

    def handler(event: Event) -> None:
        """Event handler."""
        events_received.append(event)

    event_bus.subscribe(EventType.CONVERSION_STARTED, handler)
    event_bus.emit(Event(EventType.CONVERSION_STARTED, {}))

    assert len(events_received) == 1

    event_bus.unsubscribe(EventType.CONVERSION_STARTED, handler)
    event_bus.emit(Event(EventType.CONVERSION_STARTED, {}))

    assert len(events_received) == 1  # Still 1, not 2


def test_event_bus_history() -> None:
    """Test event history."""
    event_bus = EventBus()
    event1 = Event(EventType.CONVERSION_STARTED, {})
    event2 = Event(EventType.CONVERSION_COMPLETED, {})

    event_bus.emit(event1)
    event_bus.emit(event2)

    history = event_bus.get_history()
    assert len(history) == 2

    filtered_history = event_bus.get_history(EventType.CONVERSION_STARTED)
    assert len(filtered_history) == 1
    assert filtered_history[0].event_type == EventType.CONVERSION_STARTED


def test_event_bus_enable_disable() -> None:
    """Test enabling and disabling event bus."""
    event_bus = EventBus()
    events_received = []

    def handler(event: Event) -> None:
        """Event handler."""
        events_received.append(event)

    event_bus.subscribe(EventType.CONVERSION_STARTED, handler)

    # Disable
    event_bus.disable()
    assert not event_bus.is_enabled

    event_bus.emit(Event(EventType.CONVERSION_STARTED, {}))
    assert len(events_received) == 0

    # Enable
    event_bus.enable()
    assert event_bus.is_enabled

    event_bus.emit(Event(EventType.CONVERSION_STARTED, {}))
    assert len(events_received) == 1


def test_event_bus_duplicate_subscribe() -> None:
    """Test that duplicate subscription raises error."""
    event_bus = EventBus()

    def handler(event: Event) -> None:
        """Event handler."""
        pass

    event_bus.subscribe(EventType.CONVERSION_STARTED, handler)
    with pytest.raises(ValueError, match="already subscribed"):
        event_bus.subscribe(EventType.CONVERSION_STARTED, handler)

