# MarkItDown GUI

Modern graphical user interface for MarkItDown - A powerful utility tool for converting various file formats to Markdown.

## 📋 Overview

The MarkItDown GUI provides a comprehensive, user-friendly graphical interface for MarkItDown, allowing users to convert files to Markdown visually and intuitively, without needing to use the command line. The application features a modern architecture, advanced workspace management, batch processing, cloud storage integration, and platform export capabilities.

## ✨ Key Features

### ✅ Core Features
- **Modern UI with CustomTkinter**: Beautiful, modern interface with dark/light themes
- **MVC/MVP Architecture**: Clean separation of concerns with Observer pattern and Event Bus
- **Advanced Workspace System**: Multiple tabs, independent workspaces, state persistence
- **Batch Processing**: Queue-based processing with parallel execution, retry mechanism, and advanced filtering
- **Template System**: Jinja2 templates for Markdown customization with post-processing pipeline
- **Markdown Preview**: Rich preview with syntax highlighting, extensions (tables, math, Mermaid), and themes
- **Document Comparison**: Side-by-side comparison with visual diff and statistics
- **Plugin System**: Extensible plugin architecture with hot reload and sandboxing
- **Cloud Storage Integration**: Google Drive, Dropbox, OneDrive, and AWS S3 support
- **Platform Exporters**: Direct export to Notion, Confluence, WordPress, Medium, GitHub Wiki, and Obsidian

### ✅ Advanced Features
- **Configuration System**: Profile-based configurations with hot reload
- **Drag & Drop**: File drag and drop support
- **Keyboard Shortcuts**: Comprehensive keyboard shortcuts
- **Real-time Statistics**: Conversion speed, success rate, ETA
- **Conflict Resolution**: Cloud sync conflict resolution
- **Export History**: Track all exports with filtering
- **Offline Mode**: Queue operations when offline

## 🚀 Installation

### Prerequisites

- Python 3.10 or higher
- MarkItDown installed (will be installed automatically as dependency)

### Installation Options

#### Option 1: Using requirements-gui.txt

```bash
pip install -r requirements-gui.txt
```

#### Option 2: Install as Package

```bash
# Development mode
pip install -e .

# Or using pip directly
pip install .
```

#### Option 3: With Development Dependencies

```bash
pip install -e ".[dev]"
```

## 📁 Project Structure

```
markitdown/
├── gui/                          # Main GUI directory
│   ├── core/                     # Core architecture components
│   │   ├── app.py                # Main application class
│   │   ├── events.py             # Event system
│   │   ├── observer.py           # Observer pattern
│   │   ├── state.py              # State management
│   │   ├── workspace.py          # Workspace management
│   │   ├── batch_processor.py    # Batch processing
│   │   ├── templates.py          # Template system
│   │   ├── markdown_renderer.py  # Markdown rendering
│   │   ├── document_comparator.py # Document comparison
│   │   ├── plugin_system.py      # Plugin system
│   │   ├── cloud_storage.py     # Cloud storage
│   │   └── exporters.py         # Platform exporters
│   ├── models/                   # Business logic layer
│   │   └── conversion_model.py
│   ├── views/                    # UI components
│   │   ├── main_window.py
│   │   ├── modern_window.py
│   │   ├── workspace_window.py
│   │   ├── batch_window.py
│   │   ├── template_window.py
│   │   ├── preview_window.py
│   │   ├── comparison_window.py
│   │   ├── plugin_window.py
│   │   ├── cloud_window.py
│   │   └── export_window.py
│   ├── controllers/              # Controllers
│   │   └── conversion_controller.py
│   ├── components/               # Reusable UI components
│   │   ├── workspace_tabs.py
│   │   ├── split_view.py
│   │   ├── batch_ui.py
│   │   ├── template_editor.py
│   │   ├── markdown_preview.py
│   │   ├── diff_viewer.py
│   │   ├── plugin_manager_ui.py
│   │   ├── cloud_explorer.py
│   │   └── export_ui.py
│   ├── integrations/             # Cloud storage integrations
│   │   ├── google_drive.py
│   │   ├── dropbox_provider.py
│   │   ├── onedrive_provider.py
│   │   └── aws_s3_provider.py
│   ├── exporters/                 # Platform exporters
│   │   ├── notion_exporter.py
│   │   ├── confluence_exporter.py
│   │   ├── wordpress_exporter.py
│   │   ├── medium_exporter.py
│   │   ├── github_wiki_exporter.py
│   │   └── obsidian_exporter.py
│   ├── plugins/                   # Example plugins
│   │   ├── ocr_plugin.py
│   │   ├── notion_plugin.py
│   │   └── git_plugin.py
│   ├── utils/                     # Utilities and helpers
│   ├── config/                    # Configuration files
│   └── assets/                     # Icons, images, static assets
├── requirements-gui.txt          # GUI-specific dependencies
├── pyproject.toml                 # Package configuration
└── README-GUI.md                  # This file
```

## 🎯 Features in Detail

### Modern UI with CustomTkinter

- **Retractable Sidebar**: Navigation menu with icons
- **Tabbed Workspace**: Multiple workspaces with independent state
- **Preview Panel**: Toggle-able preview panel
- **Status Bar**: Real-time information display
- **Top Bar**: User profile and quick settings
- **Theme Switching**: Dark/light mode with smooth transitions
- **Responsive Layout**: Intelligent resizing
- **Tooltips**: Informative tooltips
- **Keyboard Shortcuts**: Full keyboard navigation
- **Drag & Drop**: File drag and drop support
- **Animations**: Subtle animations for better UX
- **Accessibility**: Keyboard navigation support

### Advanced Workspace System

- **Dynamic Tabs**: Add/remove tabs dynamically
- **Independent Workspaces**: Each tab is an independent workspace
- **State Persistence**: Save/restore workspace state
- **Conversion History**: History per workspace
- **Side-by-Side Comparison**: Split view for comparison
- **Custom Tab Naming**: Custom names and colors for tabs
- **Tab Reordering**: Drag tabs to reorder
- **Close Confirmation**: Confirm before closing tabs
- **Visual Indicators**: Status indicators (processing, error, success)
- **Keyboard Shortcuts**: Ctrl+T (new), Ctrl+W (close), Ctrl+Tab (navigate)

### Batch Processing System

- **Conversion Queue**: Priority-based queue
- **Parallel Processing**: ThreadPoolExecutor/ProcessPoolExecutor
- **Configurable Workers**: Limit number of workers
- **Pause/Resume**: Pause and resume processing
- **Cancel Operations**: Cancel individual or all conversions
- **Automatic Retry**: Exponential backoff retry mechanism
- **Duplicate Detection**: Detect and handle duplicate files
- **Advanced Filtering**: Filter by extension, size, date, regex
- **File Exclusion**: Exclude specific files or folders
- **Preview List**: Preview file list before processing
- **Time Estimation**: Estimate remaining time
- **Real-time Statistics**: Speed, success rate, progress

### Template and Post-processing System

- **Jinja2 Templates**: Custom Markdown structure
- **Header/Footer**: Custom headers and footers
- **Metadata**: Author, date, tags support
- **Automatic TOC**: Table of contents generation
- **Code Formatting**: Custom code block formatting
- **Table Styles**: Custom table styles
- **Post-processing**: Whitespace cleanup, link normalization, regex substitutions
- **Template Library**: Predefined templates (Technical, Blog, Academic, Minimalist)
- **Template Editor**: Integrated template editor
- **Real-time Preview**: Preview templates in real-time
- **Import/Export**: Import and export templates
- **Syntax Validation**: Validate template syntax

### Markdown Preview System

- **HTML Rendering**: Markdown to HTML using markdown-it-py
- **Syntax Highlighting**: Code highlighting with Pygments
- **Markdown Extensions**: Tables, Footnotes, Task lists, Emoji, Math (KaTeX), Mermaid diagrams
- **Split View**: Markdown | Preview side-by-side
- **Scroll Synchronization**: Synchronized scrolling
- **Presentation Mode**: Fullscreen presentation mode
- **Export Preview**: Export as HTML/PDF
- **Preview Themes**: GitHub, ReadTheDocs, and more
- **Zoom**: Zoom in/out functionality
- **Dark/Light Mode**: Theme switching for preview
- **Search**: Search within preview
- **Copy HTML**: Copy generated HTML

### Document Comparison Tool

- **Side-by-Side View**: Original document and generated Markdown
- **Visual Diff**: Color-coded differences (green: added, red: removed, yellow: modified)
- **Navigation**: Navigate through differences (next/previous)
- **Conversion Statistics**: Content preservation %, lost elements, altered formatting
- **PDF Viewer**: Integrated PDF viewer (PyMuPDF)
- **DOCX Viewer**: Integrated DOCX viewer (python-docx)
- **Synchronized Zoom**: Synchronized zoom controls
- **Export Diff**: Export diff as HTML
- **Spotlight Mode**: Focus on differences
- **Diff Filters**: Filter by difference type

### Plugin System

- **Base Plugin API**: AbstractPlugin class with lifecycle hooks
- **Plugin Manager GUI**: List, install, activate, deactivate, configure plugins
- **Plugin Types**: Input processors, Output formatters, UI extensions, Integrations
- **Sandboxing**: Plugin sandboxing for security
- **Versioning**: Semantic versioning support
- **Hot Reload**: Hot reload plugins
- **Plugin Logs**: Plugin-specific logging
- **Automatic Documentation**: Auto-generated documentation
- **Example Plugins**: OCR (Tesseract), Notion Export, Git Integration

### Cloud Storage Integration

- **Google Drive**: OAuth2 authentication, file operations, bidirectional sync
- **Dropbox**: API integration, file operations, share links
- **OneDrive**: MSAL authentication, Graph API, file operations
- **AWS S3**: Bucket management, upload/download, presigned URLs
- **Unified Interface**: Cloud explorer with drag & drop
- **Sync Status**: Real-time sync status
- **Credential Management**: Secure credential storage
- **Local Cache**: Metadata caching
- **Offline Mode**: Queue operations when offline
- **Conflict Resolution**: Resolve sync conflicts

### Platform Exporters

- **Notion**: Create pages/databases, preserve hierarchy, upload images
- **Confluence**: REST API, create/update pages, spaces & permissions
- **WordPress**: Create posts/pages, categories & tags, featured images
- **Medium**: Publishing API, drafts & published
- **GitHub Wiki**: Git integration, commit & push
- **Obsidian**: Vault integration, internal links, frontmatter
- **Unified Interface**: Platform selection, field mapping, preview
- **Export History**: Track all exports
- **Templates**: Platform-specific templates

## 📝 Usage

### Running the Application

After installation, you can run the GUI using:

```bash
markitdown-gui
```

Or directly via Python:

```bash
python -m gui
```

### Basic Conversion

1. Launch the application
2. Select a file using File → Open or drag & drop
3. The file will be converted automatically
4. Preview the result in the preview panel
5. Save or export to your preferred platform

### Batch Processing

1. Go to File → Batch Processing
2. Add files or folders
3. Configure filters and options
4. Start processing
5. Monitor progress and statistics

### Using Templates

1. Go to Tools → Templates
2. Select or create a template
3. Configure post-processing rules
4. Apply template to conversion

### Exporting to Platforms

1. Convert your document
2. Go to File → Export
3. Select target platform
4. Configure field mapping
5. Preview and export

## 🔧 Configuration

The GUI uses a robust configuration system based on Pydantic for validation and YAML for persistence.

### Configuration Files

- `config.default.yaml` - Default settings
- `config.yaml` - User-specific settings
- `config.{profile}.yaml` - Profile-specific settings

### Configuration Options

- **Plugins**: Enable/disable MarkItDown plugins
- **Document Intelligence**: Configure Azure Document Intelligence endpoint
- **LLM Integration**: Configure LLM client for image descriptions
- **Themes**: Select interface theme
- **Export Preferences**: Configure export defaults
- **File Format Settings**: Format-specific settings
- **Internationalization**: Language settings

See [Configuration Documentation](gui/config/README.md) for details.

## 🧪 Testing

To run tests:

```bash
# Run all tests
pytest tests/

# Run with coverage
pytest --cov=gui tests/

# Run specific test file
pytest tests/gui/test_events.py
```

## 📚 Documentation

### Main Documentation
- [GUI README](gui/README.md) - GUI overview
- [Architecture](gui/ARCHITECTURE.md) - Architecture documentation
- [Configuration](gui/config/README.md) - Configuration system

### Feature Documentation
- [Workspace System](gui/views/WORKSPACE-SYSTEM-README.md)
- [Batch Processing](gui/views/BATCH-PROCESSING-README.md)
- [Template System](gui/views/TEMPLATE-SYSTEM-README.md)
- [Preview System](gui/views/PREVIEW-SYSTEM-README.md)
- [Comparison System](gui/views/COMPARISON-SYSTEM-README.md)
- [Plugin System](gui/views/PLUGIN-SYSTEM-README.md)
- [Cloud Storage](gui/views/CLOUD-STORAGE-README.md)
- [Export System](gui/views/EXPORT-SYSTEM-README.md)

## 🤝 Contributing

Contributions are welcome! Please:

1. Fork the repository
2. Create a branch for your feature (`git checkout -b feature/new-feature`)
3. Commit your changes (`git commit -am 'Add new feature'`)
4. Push to the branch (`git push origin feature/new-feature`)
5. Open a Pull Request

## 📄 License

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.

## 🔗 Links

- [Main MarkItDown Repository](https://github.com/microsoft/markitdown)
- [MarkItDown Documentation](../README.md)
- [Issues](https://github.com/microsoft/markitdown/issues)

## 📞 Support

For questions and support:
- Open an issue on GitHub
- Consult the main MarkItDown documentation
- See [SUPPORT.md](SUPPORT.md) for more information

## 🗺️ Roadmap

### Version 1.0.0 (Current)
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

### Version 1.1.0 (Planned)
- [ ] Enhanced plugin marketplace
- [ ] More cloud storage providers
- [ ] Advanced export options
- [ ] Performance optimizations
- [ ] Additional themes

### Version 1.2.0 (Future)
- [ ] Collaborative features
- [ ] Real-time sync
- [ ] Advanced analytics
- [ ] Custom workflows
- [ ] API for automation

---

**Status**: Production-ready with comprehensive feature set! 🎉
