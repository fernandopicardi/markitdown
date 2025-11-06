# Advanced Workspace System

## Overview

The MarkItDown GUI features an advanced workspace system that allows multiple concurrent conversions with independent state management, persistence, and comparison capabilities.

## Features

### ✅ Dynamic Tabs
- Add/remove workspaces dynamically
- Each tab represents an independent workspace
- Tab "+" button for creating new workspaces
- Visual indicators for workspace status

### ✅ Independent Workspaces
- Each workspace maintains its own:
  - Conversion state
  - File paths
  - Result text
  - History
  - Custom settings

### ✅ State Persistence
- Automatic saving of workspace states
- Restore workspaces on application restart
- Per-workspace JSON storage
- Order preservation

### ✅ Conversion History
- Each workspace tracks its own conversion history
- View past conversions per workspace
- Compare results across time

### ✅ Split View Comparison
- Compare multiple workspaces side by side
- Up to 3 workspaces in split view
- Toggle between single and split view
- Real-time updates

### ✅ Tab Customization
- Custom names for workspaces
- Color coding per workspace
- Visual status indicators:
  - 🟢 Processing (blue)
  - ✅ Success (green)
  - ❌ Error (red)
  - ⚠️ Warning (yellow)
  - ⚪ Idle (gray)

### ✅ Tab Reordering
- Drag tabs to reorder (basic support)
- Order persistence
- Keyboard navigation

### ✅ Tab Management
- Close tabs with confirmation
- Prevent accidental data loss
- Auto-select next tab on close

### ✅ Keyboard Shortcuts
- `Ctrl+T`: New workspace
- `Ctrl+W`: Close active workspace
- `Ctrl+Tab`: Next workspace
- `Ctrl+Shift+Tab`: Previous workspace
- `Ctrl+S`: Save workspace
- `Ctrl+Shift+S`: Toggle split view

## Usage

### Creating Workspaces

```python
from gui.core.workspace import WorkspaceManager

manager = WorkspaceManager()

# Create new workspace
workspace = manager.create_workspace(
    name="My Workspace",
    color="#3498DB"
)
```

### Using Advanced Workspace Window

```python
from gui.views.workspace_window import AdvancedWorkspaceWindow
from gui.core.events import EventBus
from gui.core.workspace import WorkspaceManager

event_bus = EventBus()
workspace_manager = WorkspaceManager()

window = AdvancedWorkspaceWindow(
    event_bus=event_bus,
    workspace_manager=workspace_manager
)
window.run()
```

### Managing Workspaces

```python
# Get workspace
workspace = manager.get_workspace(workspace_id)

# Update workspace
manager.update_workspace(
    workspace_id,
    name="New Name",
    color="#E74C3C"
)

# Save workspace
manager.save_workspace(workspace_id)

# Remove workspace
manager.remove_workspace(workspace_id)
```

## Workspace State

Each workspace maintains:

```python
WorkspaceState(
    workspace_id: str          # Unique identifier
    name: str                  # Display name
    color: str                 # Color code
    created_at: datetime       # Creation timestamp
    last_modified: datetime    # Last modification
    current_conversion: ConversionState
    conversion_history: List[ConversionState]
    input_file: Optional[str]
    output_file: Optional[str]
    result_text: Optional[str]
    status: WorkspaceStatus
    error_message: Optional[str]
    settings: Dict[str, Any]
)
```

## Storage

Workspaces are stored in:
- **Windows**: `%LOCALAPPDATA%\MarkItDown\workspaces\`
- **Linux/Mac**: `~/.config/markitdown/workspaces/`

Each workspace is saved as:
- `{workspace_id}.json` - Workspace state
- `order.json` - Tab order and active workspace

## Integration with Conversion System

Workspaces integrate with the conversion system:

```python
# Conversion events include workspace_id
event_bus.emit(Event(
    EventType.FILE_SELECTED,
    {
        "input_file": "file.pdf",
        "workspace_id": workspace_id
    }
))

# Controller handles workspace-specific conversions
# Each workspace tracks its own conversion state
```

## Split View

### Enabling Split View

1. Click "Split" button in tab bar
2. Or press `Ctrl+Shift+S`
3. Workspaces with results are displayed side by side

### Features

- Compare up to 3 workspaces
- Side-by-side result display
- Real-time updates
- Easy toggle back to single view

## Visual Indicators

### Status Colors

- **Idle**: Gray - No active operation
- **Processing**: Blue - Conversion in progress
- **Success**: Green - Conversion completed successfully
- **Error**: Red - Conversion failed
- **Warning**: Yellow - Warning state

### Tab Appearance

- Color indicator bar on left
- Status dot indicator
- Workspace name
- Close button (×)

## Keyboard Shortcuts

| Shortcut | Action |
|----------|--------|
| `Ctrl+T` | New workspace |
| `Ctrl+W` | Close active workspace |
| `Ctrl+Tab` | Next workspace |
| `Ctrl+Shift+Tab` | Previous workspace |
| `Ctrl+S` | Save workspace |
| `Ctrl+Shift+S` | Toggle split view |

## Best Practices

1. **Name Workspaces**: Use descriptive names
2. **Color Coding**: Use colors to organize workspaces
3. **Save Regularly**: Workspaces auto-save, but manual save available
4. **Close Unused**: Remove workspaces you don't need
5. **Use Split View**: Compare results side by side

## Troubleshooting

### Workspaces Not Loading

- Check storage directory permissions
- Verify JSON files are valid
- Check logs for errors

### Tab Not Updating

- Call `update_workspace_tab(workspace_id)`
- Verify workspace state is updated
- Check event bus connections

### Split View Not Working

- Ensure workspaces have result text
- Check workspace count (max 3)
- Verify split view is properly initialized

## Future Enhancements

- [ ] Full drag & drop tab reordering
- [ ] Workspace templates
- [ ] Workspace groups
- [ ] Export/import workspaces
- [ ] Workspace search
- [ ] More split view layouts (2x2, etc.)

## See Also

- [Workspace Manager API](../core/workspace.py)
- [Workspace Tabs Component](../components/workspace_tabs.py)
- [Split View Component](../components/split_view.py)

