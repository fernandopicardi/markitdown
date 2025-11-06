"""
Tests for state management.
"""

import pytest
from pathlib import Path
from gui.core.state import (
    AppState,
    ConversionState,
    ConversionStatus,
    StateManager
)


def test_conversion_state() -> None:
    """Test ConversionState."""
    state = ConversionState()
    assert state.status == ConversionStatus.IDLE
    assert state.progress == 0.0
    assert not state.is_active
    assert not state.is_complete
    assert not state.has_error

    state.status = ConversionStatus.IN_PROGRESS
    assert state.is_active

    state.status = ConversionStatus.COMPLETED
    assert state.is_complete

    state.status = ConversionStatus.FAILED
    assert state.has_error


def test_conversion_state_reset() -> None:
    """Test resetting conversion state."""
    state = ConversionState()
    state.input_file = Path("test.pdf")
    state.status = ConversionStatus.COMPLETED
    state.progress = 1.0

    state.reset()
    assert state.input_file is None
    assert state.status == ConversionStatus.IDLE
    assert state.progress == 0.0


def test_app_state() -> None:
    """Test AppState."""
    state = AppState()
    assert len(state.recent_files) == 0
    assert state.enable_plugins is False
    assert state.theme == "default"

    # Test settings
    state.set_setting("test_key", "test_value")
    assert state.get_setting("test_key") == "test_value"
    assert state.get_setting("nonexistent", "default") == "default"


def test_app_state_recent_files() -> None:
    """Test recent files management."""
    state = AppState()
    file1 = Path("file1.pdf")
    file2 = Path("file2.pdf")

    state.add_recent_file(file1)
    assert len(state.recent_files) == 1
    assert state.recent_files[0] == file1

    state.add_recent_file(file2)
    assert len(state.recent_files) == 2
    assert state.recent_files[0] == file2  # Most recent first

    # Adding same file again should move it to front
    state.add_recent_file(file1)
    assert len(state.recent_files) == 2
    assert state.recent_files[0] == file1


def test_state_manager() -> None:
    """Test StateManager."""
    manager = StateManager()
    assert manager.state is not None

    # Test state update
    def updater(state: AppState) -> None:
        state.theme = "dark"

    manager.update_state(updater)
    assert manager.state.theme == "dark"


def test_state_manager_observer() -> None:
    """Test StateManager observer pattern."""
    from gui.core.observer import Observer

    class TestObserver(Observer):
        def __init__(self) -> None:
            self.update_count = 0
            self.last_state = None

        def update(self, subject, event=None) -> None:
            self.update_count += 1
            self.last_state = event

    manager = StateManager()
    observer = TestObserver()

    manager.attach_observer(observer)
    assert observer.update_count == 0

    def updater(state: AppState) -> None:
        state.theme = "dark"

    manager.update_state(updater)
    assert observer.update_count == 1
    assert isinstance(observer.last_state, AppState)
    assert observer.last_state.theme == "dark"


def test_state_manager_callback() -> None:
    """Test StateManager with callback function."""
    manager = StateManager()
    updates = []

    def callback(subject, event) -> None:
        updates.append(event)

    manager.attach_observer(callback)

    def updater(state: AppState) -> None:
        state.theme = "dark"

    manager.update_state(updater)
    assert len(updates) == 1


def test_state_manager_undo() -> None:
    """Test state undo functionality."""
    manager = StateManager()
    initial_theme = manager.state.theme

    def updater1(state: AppState) -> None:
        state.theme = "dark"

    def updater2(state: AppState) -> None:
        state.theme = "light"

    manager.update_state(updater1)
    manager.update_state(updater2)

    assert manager.state.theme == "light"
    assert manager.can_undo()

    manager.undo()
    assert manager.state.theme == "dark"

    manager.undo()
    assert manager.state.theme == initial_theme
    assert not manager.can_undo()


def test_state_manager_conversion_state() -> None:
    """Test conversion state management."""
    manager = StateManager()
    conversion = ConversionState()
    conversion.input_file = Path("test.pdf")
    conversion.status = ConversionStatus.IN_PROGRESS

    manager.set_conversion_state(conversion)
    assert manager.state.current_conversion.input_file == Path("test.pdf")
    assert manager.state.current_conversion.status == ConversionStatus.IN_PROGRESS

    manager.reset_conversion()
    assert manager.state.current_conversion.status == ConversionStatus.IDLE

