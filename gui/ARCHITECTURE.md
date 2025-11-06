# MarkItDown GUI Architecture

This document describes the architecture of the MarkItDown GUI application, which follows the MVC/MVP pattern with additional architectural patterns for decoupled communication.

## Architecture Overview

The application is structured using the **Model-View-Controller (MVC)** pattern with the following layers:

```
┌─────────────────────────────────────────────────────────┐
│                    Application Layer                     │
│                  (gui/core/app.py)                       │
└─────────────────────────────────────────────────────────┘
                            │
        ┌───────────────────┼───────────────────┐
        │                   │                   │
┌───────▼──────┐   ┌────────▼────────┐   ┌─────▼──────┐
│    Model     │   │   Controller    │   │    View    │
│              │   │                 │   │            │
│ conversion_  │   │ conversion_     │   │ main_      │
│ model.py     │   │ controller.py   │   │ window.py  │
└───────┬──────┘   └────────┬────────┘   └─────┬──────┘
        │                   │                   │
        └───────────────────┼───────────────────┘
                            │
        ┌───────────────────┼───────────────────┐
        │                   │                   │
┌───────▼──────┐   ┌────────▼────────┐   ┌─────▼──────┐
│   Observer   │   │   Event Bus     │   │   State    │
│   Pattern    │   │                 │   │  Manager   │
│              │   │  events.py      │   │ state.py   │
│ observer.py  │   │                 │   │            │
└──────────────┘   └─────────────────┘   └────────────┘
```

## Core Components

### 1. Core Architecture (`gui/core/`)

#### Observer Pattern (`observer.py`)
- **Observable**: Base class for objects that notify observers of changes
- **Observer**: Abstract base class for objects that receive notifications
- **EventObserver**: Bridges Observer pattern with Event system

#### Event System (`events.py`)
- **EventType**: Enumeration of all event types
- **Event**: Immutable event data structure
- **EventBus**: Central event bus for publish-subscribe communication

#### State Management (`state.py`)
- **AppState**: Central application state (single source of truth)
- **ConversionState**: State for individual conversion operations
- **StateManager**: Manages state with change notifications

#### Application (`app.py`)
- **MarkItDownApp**: Main application class that initializes and coordinates all components

### 2. Model Layer (`gui/models/`)

#### ConversionModel (`conversion_model.py`)
- Encapsulates business logic for file conversion
- Uses MarkItDown library for actual conversion
- Supports async/await for non-blocking operations
- Implements Observable pattern for state changes

**Responsibilities:**
- File conversion operations
- Progress tracking
- Error handling
- Integration with MarkItDown library

### 3. View Layer (`gui/views/`)

#### MainWindow (`main_window.py`)
- Implements the user interface using Tkinter
- Implements Observer pattern to receive state updates
- Subscribes to events for UI updates
- Handles user input and displays results

**Responsibilities:**
- UI rendering
- User input handling
- Displaying conversion results
- Progress visualization

### 4. Controller Layer (`gui/controllers/`)

#### ConversionController (`conversion_controller.py`)
- Coordinates between Model and View
- Handles user actions
- Updates state through StateManager
- Emits events for cross-component communication

**Responsibilities:**
- User action handling
- Model-View coordination
- State updates
- Event emission

## Communication Patterns

### 1. Observer Pattern
Used for direct one-to-many communication:
- StateManager → Observers (View, Controller)
- ConversionModel → Observers

### 2. Event Bus Pattern
Used for decoupled publish-subscribe communication:
- Components emit events without knowing subscribers
- Multiple components can subscribe to same events
- Global event handlers for application-wide events

### 3. State Management
- Single source of truth (AppState)
- All state changes go through StateManager
- State changes trigger notifications to observers
- Supports undo/redo functionality

## Data Flow

### Conversion Flow

```
User Action (View)
    │
    ▼
Controller receives action
    │
    ▼
Controller updates StateManager
    │
    ▼
StateManager notifies Observers (View, Controller)
    │
    ▼
Controller starts conversion in Model
    │
    ▼
Model emits progress events
    │
    ▼
Controller updates StateManager with progress
    │
    ▼
View updates UI from State
    │
    ▼
Model completes conversion
    │
    ▼
Controller updates StateManager with result
    │
    ▼
View displays result
```

## Key Design Decisions

### 1. MVC/MVP Pattern
- **Separation of Concerns**: Clear separation between data (Model), presentation (View), and logic (Controller)
- **Testability**: Each layer can be tested independently
- **Maintainability**: Changes in one layer don't affect others

### 2. Observer Pattern
- **Decoupling**: Components don't need direct references to each other
- **Flexibility**: Easy to add/remove observers
- **Reactivity**: Automatic updates when state changes

### 3. Event Bus
- **Loose Coupling**: Components communicate through events, not direct calls
- **Scalability**: Easy to add new event types and handlers
- **Debugging**: Event history for troubleshooting

### 4. Centralized State
- **Single Source of Truth**: All state in one place
- **Predictability**: State changes are explicit and traceable
- **Undo/Redo**: Built-in support for state history

### 5. Async/Await
- **Non-blocking**: UI remains responsive during conversions
- **Progress Updates**: Real-time progress feedback
- **Cancellation**: Support for cancelling long operations

## Type Safety

All components use:
- **Type Hints**: Full type annotations for all functions and methods
- **Dataclasses**: For structured data (Event, AppState, ConversionState)
- **Enums**: For type-safe constants (EventType, ConversionStatus)

## Testing Strategy

### Unit Tests
- Test each component in isolation
- Mock dependencies
- Test edge cases and error conditions

### Integration Tests
- Test component interactions
- Test event flow
- Test state management

### Test Structure
```
tests/
└── gui/
    ├── test_observer.py      # Observer pattern tests
    ├── test_events.py         # Event system tests
    ├── test_state.py          # State management tests
    ├── test_conversion_model.py  # Model tests
    └── conftest.py            # Pytest fixtures
```

## Extension Points

### Adding New Features

1. **New Event Types**: Add to `EventType` enum in `events.py`
2. **New State Fields**: Add to `AppState` or create new state class
3. **New UI Components**: Add to `views/` and subscribe to events
4. **New Controllers**: Add to `controllers/` and coordinate Model/View
5. **New Models**: Add to `models/` and implement Observable pattern

### Adding Plugins

The architecture supports plugins through:
- Event system (plugins can subscribe to events)
- Observer pattern (plugins can observe state changes)
- Extension points in Model layer

## Best Practices

1. **Always use StateManager for state changes** - Don't modify state directly
2. **Emit events for cross-component communication** - Don't use direct method calls
3. **Use type hints everywhere** - Improves code quality and IDE support
4. **Handle errors gracefully** - Emit error events, don't crash
5. **Log important operations** - Use the logging module
6. **Write tests** - Maintain test coverage for all components

## Future Enhancements

- [ ] Settings dialog with persistent storage
- [ ] Plugin system UI
- [ ] Batch conversion support
- [ ] Conversion history viewer
- [ ] Export/import settings
- [ ] Theme customization
- [ ] Internationalization (i18n)

