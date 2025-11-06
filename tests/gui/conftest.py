"""
Pytest configuration and fixtures for GUI tests.
"""

import pytest
from pathlib import Path
from gui.core.events import EventBus
from gui.core.state import StateManager
from gui.models.conversion_model import ConversionModel


@pytest.fixture
def event_bus() -> EventBus:
    """Create an event bus for testing."""
    return EventBus()


@pytest.fixture
def state_manager() -> StateManager:
    """Create a state manager for testing."""
    return StateManager()


@pytest.fixture
def conversion_model(event_bus: EventBus) -> ConversionModel:
    """Create a conversion model for testing."""
    try:
        return ConversionModel(event_bus=event_bus)
    except ImportError:
        pytest.skip("MarkItDown not installed")


@pytest.fixture
def temp_file(tmp_path: Path) -> Path:
    """Create a temporary file for testing."""
    file_path = tmp_path / "test.txt"
    file_path.write_text("Test content")
    return file_path

