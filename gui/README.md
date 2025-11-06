# MarkItDown GUI

Graphical user interface for MarkItDown - A utility tool for converting various files to Markdown.

## Architecture

The GUI follows the **MVC/MVP pattern** with additional architectural patterns:

- **Model-View-Controller (MVC)**: Clear separation of concerns
- **Observer Pattern**: For reactive state updates
- **Event Bus**: For decoupled component communication
- **Centralized State Management**: Single source of truth

See [ARCHITECTURE.md](ARCHITECTURE.md) for detailed architecture documentation.

## Quick Start

### Installation

```bash
# Install dependencies
pip install -r requirements-gui.txt

# Or install as package
pip install -e .
```

### Running the Application

```bash
# Run directly
python -m gui

# Or after installation
markitdown-gui
```

## Project Structure

```
gui/
├── core/               # Core architecture components
│   ├── app.py         # Main application class
│   ├── events.py      # Event system
│   ├── observer.py    # Observer pattern
│   └── state.py       # State management
├── models/            # Business logic layer
│   └── conversion_model.py
├── views/             # UI components
│   └── main_window.py
├── controllers/       # Controllers
│   └── conversion_controller.py
├── components/        # Reusable UI components
├── utils/             # Utilities
├── config/            # Configuration
└── assets/            # Static assets
```

## Key Features

- ✅ MVC/MVP Architecture
- ✅ Observer Pattern for reactive updates
- ✅ Event Bus for decoupled communication
- ✅ Centralized State Management
- ✅ Async/Await support for non-blocking operations
- ✅ Full Type Hints
- ✅ Comprehensive Test Suite
- ✅ Modern Python (3.10+)

## Development

### Running Tests

```bash
# Run all tests
pytest tests/

# Run with coverage
pytest --cov=gui tests/

# Run specific test file
pytest tests/gui/test_events.py
```

### Code Quality

The project uses:
- **Type Hints**: Full type annotations
- **Dataclasses**: For structured data
- **Enums**: For type-safe constants
- **Docstrings**: Comprehensive documentation

## Documentation

- [ARCHITECTURE.md](ARCHITECTURE.md) - Detailed architecture documentation
- [README-GUI.md](../README-GUI.md) - General GUI documentation
- [SETUP-GUI.md](../SETUP-GUI.md) - Setup instructions

## Contributing

See the main project [README.md](../README.md) for contribution guidelines.

## License

MIT License - See [LICENSE](../LICENSE) file.

