# Document Comparison System

## Overview

The MarkItDown GUI features a sophisticated document comparison system that allows you to compare original documents with converted Markdown, providing visual diff, statistics, and navigation.

## Features

### ✅ Side-by-Side Visualization
- **Left Panel**: Original document (PDF/DOCX/Text)
- **Right Panel**: Converted Markdown
- **Synchronized View**: Both panels visible simultaneously
- **Scroll Sync**: Synchronized scrolling (optional)

### ✅ Visual Diff with Colors
- **Green**: Added content
- **Red**: Removed content
- **Yellow**: Modified content
- **White**: Unchanged content
- **Visual Markers**: Text markers for differences

### ✅ Navigation Between Differences
- **Next/Previous**: Navigate between differences
- **Diff Counter**: Current difference position
- **Jump to Difference**: Quick navigation
- **Highlight Current**: Highlight current difference

### ✅ Conversion Statistics
- **Preservation Percentage**: % of content preserved
- **Character Counts**: Original vs converted sizes
- **Difference Counts**: Added, removed, modified segments
- **Elements Lost**: List of lost elements (images, tables, etc.)
- **Formatting Changes**: Detected formatting changes

### ✅ PDF Viewer Integration
- **PyMuPDF**: Native PDF viewing
- **Page Navigation**: Previous/next page
- **Zoom Controls**: Zoom in/out
- **Page Counter**: Current page display

### ✅ DOCX Viewer Integration
- **python-docx**: DOCX text extraction
- **Text Display**: Formatted text view
- **Zoom Controls**: Adjustable zoom
- **Paragraph Rendering**: Preserve structure

### ✅ Synchronized Zoom
- **Unified Zoom**: Same zoom level for both panels
- **Zoom Controls**: Global zoom controls
- **Zoom Range**: 50% to 200%
- **Zoom Display**: Current zoom percentage

### ✅ Export Diff as HTML
- **HTML Export**: Export diff visualization
- **Complete HTML**: Full document with styles
- **Color Coding**: Preserved colors in HTML
- **Statistics Included**: Statistics in export

### ✅ Spotlight Mode
- **Focus on Differences**: Hide unchanged content
- **Highlight Changes**: Only show differences
- **Toggle**: Easy on/off
- **Clean View**: Distraction-free comparison

### ✅ Diff Filters
- **Filter by Type**: Show only specific diff types
- **All Differences**: Show all differences
- **Added Only**: Show only additions
- **Removed Only**: Show only removals
- **Modified Only**: Show only modifications

## Usage

### Basic Comparison

```python
from gui.views.comparison_window import show_comparison
from pathlib import Path

# Compare documents
show_comparison(
    original_path=Path("document.pdf"),
    converted_text="# Converted Markdown\n\nContent..."
)
```

### Using DocumentComparator

```python
from gui.core.document_comparator import DocumentComparator
from pathlib import Path

# Create comparator
comparator = DocumentComparator()

# Load original
comparator.load_original(Path("document.pdf"))

# Set converted
comparator.set_converted("# Markdown\n\nContent")

# Compare
stats = comparator.compare()

# Get statistics
print(f"Preservation: {stats.preservation_percentage:.1f}%")
print(f"Differences: {stats.total_differences}")
```

### Export Diff HTML

```python
# Export diff visualization
comparator.export_diff_html(Path("diff.html"))
```

### Navigation

```python
# Get next difference
next_idx = comparator.get_next_difference(current_index)

# Get previous difference
prev_idx = comparator.get_previous_difference(current_index)

# Get filtered segments
added_segments = comparator.get_diff_segments(DiffType.ADDED)
```

## Document Viewers

### PDF Viewer

```python
from gui.components.document_viewer import PDFViewer

viewer = PDFViewer(parent)
viewer.load_pdf(Path("document.pdf"))
viewer.set_zoom(1.5)  # 150% zoom
```

### DOCX Viewer

```python
from gui.components.document_viewer import DOCXViewer

viewer = DOCXViewer(parent)
viewer.load_docx(Path("document.docx"))
viewer.set_zoom(1.2)  # 120% zoom
```

## Diff Types

### Added (Green)
- New content in converted document
- Marked with `[+]` marker
- Green background in HTML export

### Removed (Red)
- Content removed in conversion
- Marked with `[-]` marker
- Red background in HTML export

### Modified (Yellow)
- Content changed during conversion
- Marked with `[~]` marker
- Yellow background in HTML export

### Unchanged (White)
- Content preserved exactly
- No marker
- White background

## Statistics

### Preservation Percentage
```
Preservation = (Preserved Characters / Original Characters) * 100
```

### Character Counts
- **Original Size**: Total characters in original
- **Converted Size**: Total characters in converted
- **Preserved**: Characters unchanged
- **Added**: New characters
- **Removed**: Deleted characters
- **Modified**: Changed characters

### Difference Counts
- **Total Differences**: All differences found
- **Added Segments**: Number of additions
- **Removed Segments**: Number of removals
- **Modified Segments**: Number of modifications

### Elements Lost
- **Images**: Missing images
- **Tables**: Missing tables
- **Links**: Missing links
- **Other**: Other lost elements

### Formatting Changes
- **Bold**: Bold formatting changes
- **Italic**: Italic formatting changes
- **Other**: Other formatting changes

## Integration

### With Conversion System

```python
from gui.models.conversion_model import ConversionModel
from gui.views.comparison_window import show_comparison

# Convert file
model = ConversionModel(event_bus)
result = model.convert(Path("document.pdf"))

# Show comparison
show_comparison(
    original_path=Path("document.pdf"),
    converted_text=result.result_text
)
```

### With Batch Processing

```python
# Compare after batch conversion
for task in batch_tasks:
    result = process_task(task)
    show_comparison(
        original_path=task.input_file,
        converted_text=result.content
    )
```

## Keyboard Shortcuts

- **Ctrl+N**: Next difference
- **Ctrl+P**: Previous difference
- **Ctrl+E**: Export diff HTML
- **Ctrl+Z**: Zoom in
- **Ctrl+-**: Zoom out
- **Ctrl+F**: Focus search

## Best Practices

1. **Load Both Documents**: Ensure both original and converted are loaded
2. **Use Filters**: Filter by diff type for focused analysis
3. **Spotlight Mode**: Use spotlight for quick difference review
4. **Check Statistics**: Review statistics for overall quality
5. **Export HTML**: Export for sharing or documentation
6. **Navigate Differences**: Use navigation for systematic review
7. **Zoom Appropriately**: Adjust zoom for readability

## Troubleshooting

### PDF Not Loading
- Check if PyMuPDF is installed: `pip install pymupdf`
- Verify PDF file is not corrupted
- Check file permissions

### DOCX Not Loading
- Check if python-docx is installed: `pip install python-docx`
- Verify DOCX file is valid
- Check file permissions

### Diff Not Showing
- Ensure both documents are loaded
- Run comparison after loading
- Check if documents have content

### Statistics Not Accurate
- Text extraction may vary by format
- Some formatting may not be detected
- Complex structures may affect accuracy

## Dependencies

- `difflib`: Built-in Python library
- `pymupdf`: PDF viewing (optional)
- `python-docx`: DOCX viewing (optional)
- `Pillow`: Image handling

## See Also

- [Document Comparator API](../core/document_comparator.py)
- [Document Viewers](../components/document_viewer.py)
- [Diff Viewer](../components/diff_viewer.py)
- [Comparison Window](../views/comparison_window.py)

