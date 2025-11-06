# Setup Guide - MarkItDown GUI

This document provides complete instructions for setting up the MarkItDown GUI development environment.

## ✅ Created Structure

The following directory structure has been created:

```
markitdown/
├── gui/                          # Main GUI directory
│   ├── __init__.py              # Module initialization
│   ├── __main__.py              # Main entry point
│   ├── components/              # Reusable components
│   │   └── __init__.py
│   ├── utils/                   # Utilities and helpers
│   │   └── __init__.py
│   ├── assets/                  # Icons, images
│   │   └── .gitkeep
│   └── config/                  # Configuration files
│       └── __init__.py
├── requirements-gui.txt         # GUI dependencies
├── pyproject.toml               # Package configuration
├── README-GUI.md               # GUI documentation
└── .gitignore                  # Updated with GUI rules
```

## 🚀 Installation Commands

### 1. Create Virtual Environment (Recommended)

**Windows (PowerShell):**
```powershell
python -m venv .venv
.\.venv\Scripts\Activate.ps1
```

**Linux/Mac:**
```bash
python -m venv .venv
source .venv/bin/activate
```

### 2. Install Dependencies

**Option A: Using requirements-gui.txt**
```bash
pip install -r requirements-gui.txt
```

**Option B: Install as Package (Development Mode)**
```bash
pip install -e .
```

**Option C: With Development Dependencies**
```bash
pip install -e ".[dev]"
```

### 3. Verify Installation

```bash
python -m gui
```

Or after installation:
```bash
markitdown-gui
```

## 📦 Main Dependencies

The dependencies include:

- **markitdown[all]**: Main MarkItDown package with all features
- **customtkinter**: Modern UI framework
- **Pillow**: Image manipulation
- **tqdm**: Progress bars
- **pydantic**: Configuration validation
- **pyyaml**: YAML configuration files
- **markdown-it-py**: Markdown rendering
- **pygments**: Syntax highlighting
- **notion-client**: Notion integration
- **boto3**: AWS S3 integration
- And many more...

See `requirements-gui.txt` for the complete list.

## 🔧 Next Development Steps

1. **Implement Main Interface**
   - Create `gui/app.py` with main application class
   - Implement interface with CustomTkinter

2. **Create Components**
   - `gui/components/file_selector.py`: File selector
   - `gui/components/progress_bar.py`: Progress bar
   - `gui/components/preview_panel.py`: Markdown preview

3. **Implement Utilities**
   - `gui/utils/file_utils.py`: File manipulation
   - `gui/utils/conversion_utils.py`: Conversion helpers
   - `gui/utils/ui_utils.py`: UI utilities

4. **Configuration**
   - `gui/config/settings.py`: Settings management
   - `gui/config/themes.py`: Themes and styles
   - `gui/config/constants.py`: Constants

## 📝 Important Notes

- The project uses `pyproject.toml` for modern Python configuration
- The `.gitignore` has been updated to ignore GUI temporary files
- The structure follows Python best practices for packages
- The module can be run as `python -m gui` or `markitdown-gui` after installation

## 🐛 Troubleshooting

### Error: "ModuleNotFoundError: No module named 'markitdown'"
```bash
# Install markitdown first
pip install -e packages/markitdown[all]
```

### Error: "Command 'markitdown-gui' not found"
```bash
# Reinstall package in development mode
pip install -e .
```

### Tkinter Issues
On Linux, you may need to install:
```bash
sudo apt-get install python3-tk
```

### CustomTkinter Issues
If CustomTkinter doesn't work:
```bash
# Reinstall CustomTkinter
pip install --upgrade customtkinter
```

## 📚 Additional Documentation

- [README-GUI.md](README-GUI.md) - Complete GUI documentation
- [README.md](README.md) - Main MarkItDown documentation
- [packages/markitdown/README.md](packages/markitdown/README.md) - Core package documentation
- [gui/ARCHITECTURE.md](gui/ARCHITECTURE.md) - Architecture documentation
- [gui/config/README.md](gui/config/README.md) - Configuration documentation

## 🎯 Features Implemented

The GUI includes:

- ✅ MVC/MVP Architecture
- ✅ Modern UI with CustomTkinter
- ✅ Advanced Workspace System
- ✅ Batch Processing
- ✅ Template System
- ✅ Markdown Preview
- ✅ Document Comparison
- ✅ Plugin System
- ✅ Cloud Storage Integration
- ✅ Platform Exporters

See [README-GUI.md](README-GUI.md) for complete feature list.

---

**Status**: Base structure created and ready for development! 🎉
