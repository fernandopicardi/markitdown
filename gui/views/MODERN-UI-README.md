# Modern UI with CustomTkinter

## Overview

The MarkItDown GUI features a modern, responsive interface built with CustomTkinter (CTk), providing a sleek and professional user experience.

## Features

### ✅ Layout Components

1. **Retractable Sidebar**
   - Navigation menu with icons
   - Smooth collapse/expand animation
   - Quick access to main features

2. **Tabbed Workspace**
   - Convert tab: Main conversion interface
   - History tab: Conversion history
   - Settings tab: Application settings

3. **Preview Panel**
   - Real-time preview of converted content
   - Toggle visibility
   - Syntax highlighting ready

4. **Status Bar**
   - Real-time status messages
   - Progress information
   - System notifications

5. **Top Bar**
   - User profile button
   - Quick settings access
   - Theme toggle

### ✅ Theme System

- **Dark/Light Themes**: Smooth transitions
- **Custom Colors**: Configurable color schemes
- **System Integration**: Respects system theme

### ✅ Responsive Design

- **Grid Layout**: Modern grid system
- **Weighted Columns**: Intelligent resizing
- **Minimum Sizes**: Prevents UI breakage
- **Adaptive Layout**: Adjusts to window size

### ✅ User Experience

1. **Tooltips**: Informative hover tooltips
2. **Icons**: Visual indicators (PIL/Pillow support)
3. **Animations**: Smooth transitions and hover effects
4. **Keyboard Shortcuts**:
   - `Ctrl+O`: Open file
   - `Ctrl+S`: Save result
   - `Ctrl+Enter`: Start conversion
   - `Esc`: Cancel operation
   - `F5`: Refresh
   - `Tab`: Navigate between fields

5. **Drag & Drop**: Drop files directly into the window
6. **Accessibility**:
   - Keyboard navigation
   - Focus management
   - Screen reader support ready

## Installation

```bash
pip install customtkinter
pip install tkinterdnd2  # For drag & drop
```

## Usage

### Basic Usage

```python
from gui.views.modern_window import ModernMainWindow
from gui.core.events import EventBus

event_bus = EventBus()
window = ModernMainWindow(event_bus=event_bus)
window.run()
```

### With Application

The modern window is automatically used when CustomTkinter is available:

```python
from gui.core.app import create_app

app = create_app()
app.run()  # Uses ModernMainWindow if CTk is available
```

## Components

### CTkSidebar
- Retractable navigation sidebar
- Menu items with icons
- Smooth animations

### CTkStatusBar
- Status messages
- Progress indicators
- Real-time updates

### CTkTopBar
- User profile
- Quick actions
- Theme toggle

### CTkPreviewPanel
- Content preview
- Toggle visibility
- Scrollable content

### CTkTooltip
- Hover tooltips
- Configurable delay
- Auto-positioning

### CTkAnimatedButton
- Hover animations
- Smooth transitions
- Visual feedback

### CTkIconButton
- Icon support
- PIL/Pillow integration
- Customizable size

## Keyboard Shortcuts

| Shortcut | Action |
|----------|--------|
| `Ctrl+O` | Open file |
| `Ctrl+S` | Save result |
| `Ctrl+Enter` | Start conversion |
| `Esc` | Cancel operation |
| `F5` | Refresh |
| `Tab` | Next field |
| `Shift+Tab` | Previous field |

## Drag & Drop

1. Drag a file from file explorer
2. Drop it onto the window or convert tab
3. File path is automatically set
4. Output path is auto-suggested

## Theme Customization

### Programmatic

```python
import customtkinter as ctk

# Set appearance mode
ctk.set_appearance_mode("dark")  # or "light"

# Set color theme
ctk.set_default_color_theme("blue")  # or "green", "dark-blue"
```

### Via Settings

Use the settings system to persist theme preferences:

```python
from gui.config import SettingsManager

manager = SettingsManager()
manager.update(ui__theme="dark")
manager.save()
```

## Responsive Behavior

The layout automatically adjusts:

- **Sidebar**: Collapses on small screens
- **Preview Panel**: Hides when space is limited
- **Workspace**: Expands to fill available space
- **Status Bar**: Always visible at bottom

## Accessibility Features

1. **Keyboard Navigation**:
   - Tab to navigate
   - Enter to activate
   - Esc to cancel

2. **Focus Management**:
   - Visual focus indicators
   - Logical tab order
   - Focus trapping in dialogs

3. **Screen Reader Support**:
   - Semantic labels
   - ARIA attributes ready
   - Descriptive tooltips

## Customization

### Custom Themes

```python
from gui.config import ThemeConfig, SettingsManager

manager = SettingsManager()
settings = manager.get()

custom_theme = ThemeConfig(
    name="custom",
    display_name="My Theme",
    colors={
        "background": "#2C3E50",
        "foreground": "#ECF0F1",
        "primary": "#3498DB"
    }
)

settings.themes["custom"] = custom_theme
settings.ui.theme = "custom"
manager.save(settings)
```

### Custom Icons

```python
from gui.components import CTkIconButton

button = CTkIconButton(
    parent,
    icon_path="path/to/icon.png",
    icon_size=(24, 24),
    text="Button Text"
)
```

## Performance

- **Lazy Loading**: Components load on demand
- **Efficient Updates**: Only updates changed elements
- **Smooth Animations**: 60fps animations
- **Memory Efficient**: Proper cleanup

## Troubleshooting

### CustomTkinter Not Found

If CustomTkinter is not available, the application falls back to standard Tkinter:

```python
# Automatic fallback in app.py
try:
    self.view = ModernMainWindow(...)
except ImportError:
    self.view = MainWindow(...)  # Standard Tkinter
```

### Drag & Drop Not Working

Install tkinterdnd2:

```bash
pip install tkinterdnd2
```

### Theme Not Applying

1. Check CustomTkinter version (>=5.2.0)
2. Verify theme name in settings
3. Restart application

## Future Enhancements

- [ ] More theme options
- [ ] Custom icon sets
- [ ] Advanced animations
- [ ] Multi-monitor support
- [ ] Touch gestures
- [ ] Voice commands

## See Also

- [CustomTkinter Documentation](https://customtkinter.tomschimansky.com/)
- [GUI Architecture](../ARCHITECTURE.md)
- [Configuration System](../config/README.md)

