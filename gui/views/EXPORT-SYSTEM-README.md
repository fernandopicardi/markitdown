# Platform Export System

## Overview

The MarkItDown GUI features comprehensive platform export capabilities, allowing you to export converted Markdown directly to popular platforms: Notion, Confluence, WordPress, Medium, GitHub Wiki, and Obsidian.

## Features

### ✅ Notion
- **Create Pages/Databases**: Export to Notion pages or databases
- **Hierarchy Preservation**: Maintain document structure
- **Formatting**: Preserve Markdown formatting
- **Image Upload**: Upload images to Notion
- **Notion API**: Full Notion API integration

### ✅ Confluence
- **REST API**: Confluence REST API integration
- **Create/Update Pages**: Create new or update existing pages
- **Spaces & Permissions**: Support for spaces and permissions
- **HTML Conversion**: Markdown to Confluence storage format

### ✅ WordPress
- **Create Posts/Pages**: Export as posts or pages
- **Categories & Tags**: Support for categories and tags
- **Featured Images**: Set featured images
- **Status Control**: Draft or published status
- **REST API**: WordPress REST API

### ✅ Medium
- **Publishing API**: Medium Publishing API
- **Drafts & Published**: Control publication status
- **Tags**: Support for tags
- **HTML Format**: Markdown to HTML conversion

### ✅ GitHub Wiki
- **Git Integration**: Full Git integration
- **Commit & Push**: Automatic commit and push
- **Wiki Format**: Native Markdown format
- **Version Control**: Full version control support

### ✅ Obsidian
- **Vault Integration**: Direct vault integration
- **Internal Links**: Process Obsidian-style links
- **Frontmatter**: YAML frontmatter support
- **Local Files**: Direct file system access

### ✅ Unified Interface
- **Platform Selection**: Easy platform selection
- **Field Mapping**: Custom field mapping
- **Preview**: Preview before export
- **Export History**: Track export history
- **Templates**: Platform-specific templates

## Usage

### Basic Export

```python
from gui.core.exporters import ExportManager, ExportPlatform
from gui.exporters import NotionExporter
from gui.views.export_window import show_export_window

# Create manager
manager = ExportManager()

# Register exporter
manager.register_exporter(NotionExporter())

# Authenticate
manager.authenticate_exporter(
    ExportPlatform.NOTION,
    {"notion_token": "your_token"}
)

# Export
result = manager.export_to_platform(
    ExportPlatform.NOTION,
    markdown_text,
    {"title": "My Document", "author": "John Doe"},
    destination="database_id"  # Optional
)

# Show export window
show_export_window(markdown_text, metadata)
```

### Notion Export

```python
from gui.exporters import NotionExporter

exporter = NotionExporter()
exporter.authenticate({"notion_token": "your_token"})

result = exporter.export(
    markdown_text,
    {"title": "My Page", "author": "John"},
    destination="database_id"  # Optional
)

print(f"Page URL: {result.exported_url}")
```

### Confluence Export

```python
from gui.exporters import ConfluenceExporter

exporter = ConfluenceExporter()
exporter.authenticate({
    "base_url": "https://your-domain.atlassian.net",
    "username": "user@example.com",
    "api_token": "your_token"
})

result = exporter.export(
    markdown_text,
    {"title": "My Page", "space_key": "SPACE"},
    destination="SPACE:Page Title"
)
```

### WordPress Export

```python
from gui.exporters import WordPressExporter

exporter = WordPressExporter()
exporter.authenticate({
    "base_url": "https://your-site.com",
    "username": "admin",
    "application_password": "your_app_password"
})

result = exporter.export(
    markdown_text,
    {
        "title": "My Post",
        "status": "draft",
        "categories": ["Tech", "Blog"],
        "tags": ["python", "markdown"]
    }
)
```

### Medium Export

```python
from gui.exporters import MediumExporter

exporter = MediumExporter()
exporter.authenticate({"access_token": "your_token"})

result = exporter.export(
    markdown_text,
    {
        "title": "My Article",
        "status": "draft",  # or "public"
        "tags": ["technology", "programming"]
    }
)
```

### GitHub Wiki Export

```python
from gui.exporters import GitHubWikiExporter

exporter = GitHubWikiExporter()
exporter.authenticate({
    "wiki_path": "/path/to/wiki",
    "wiki_url": "https://github.com/user/repo.wiki.git"
})

result = exporter.export(
    markdown_text,
    {
        "title": "My Wiki Page",
        "commit_message": "Add new page"
    },
    destination="my-page.md"
)
```

### Obsidian Export

```python
from gui.exporters import ObsidianExporter

exporter = ObsidianExporter()
exporter.authenticate({"vault_path": "/path/to/vault"})

result = exporter.export(
    markdown_text,
    {
        "title": "My Note",
        "tags": ["note", "important"],
        "author": "John Doe"
    },
    destination="my-note.md"
)
```

## Field Mapping

### Custom Mapping

```python
from gui.core.exporters import ExportMapping

mapping = ExportMapping(
    title_field="title",
    author_field="author",
    tags_field="tags",
    date_field="date",
    custom_fields={
        "category": "category",
        "status": "status"
    }
)

exporter.set_mapping(mapping)
```

## Export Manager

### Managing Exports

```python
from gui.core.exporters import ExportManager

manager = ExportManager()

# Register exporters
manager.register_exporter(NotionExporter())
manager.register_exporter(ConfluenceExporter())

# Authenticate
manager.authenticate_exporter(ExportPlatform.NOTION, {...})

# Export
result = manager.export_to_platform(
    ExportPlatform.NOTION,
    markdown_text,
    metadata
)

# Get history
history = manager.get_history(ExportPlatform.NOTION)
```

## Authentication

### Notion
1. Create integration in Notion
2. Get integration token
3. Share database/page with integration
4. Use token in credentials

### Confluence
1. Generate API token in Atlassian account
2. Use base URL, username, and API token
3. Ensure proper permissions

### WordPress
1. Create Application Password in WordPress
2. Use site URL, username, and application password
3. Ensure REST API is enabled

### Medium
1. Generate access token from Medium
2. Use access token in credentials
3. Token provides user ID automatically

### GitHub Wiki
1. Clone wiki repository locally
2. Provide wiki path or URL
3. Ensure Git is configured

### Obsidian
1. Provide vault path
2. Ensure vault exists
3. Write permissions required

## Integration

### With Conversion

```python
from gui.models.conversion_model import ConversionModel
from gui.core.exporters import ExportManager, ExportPlatform

# Convert document
model = ConversionModel(event_bus)
result = model.convert(Path("document.pdf"))

# Export to platform
export_manager = ExportManager()
export_manager.export_to_platform(
    ExportPlatform.NOTION,
    result.markdown,
    {
        "title": result.metadata.get("title", "Document"),
        "source_file": "document.pdf"
    }
)
```

### With Batch Processing

```python
# Process and export in batch
for file in files:
    # Convert
    result = convert_file(file)
    
    # Export
    export_manager.export_to_platform(
        ExportPlatform.WORDPRESS,
        result.markdown,
        {"title": result.title}
    )
```

## Best Practices

1. **Authenticate First**: Always authenticate before export
2. **Preview Content**: Use preview before exporting
3. **Field Mapping**: Configure field mapping for consistency
4. **Error Handling**: Handle export errors gracefully
5. **History Tracking**: Review export history regularly
6. **Templates**: Use platform-specific templates
7. **Test Exports**: Test with drafts before publishing

## Troubleshooting

### Authentication Fails
- Check credentials
- Verify API permissions
- Review platform-specific requirements

### Export Fails
- Check content format
- Verify destination exists
- Review error messages
- Check network connectivity

### Formatting Issues
- Review Markdown conversion
- Check platform-specific formatting
- Adjust field mapping

## Dependencies

- `notion-client`: Notion API
- `requests`: HTTP requests
- `markdown`: Markdown to HTML
- `GitPython`: Git operations
- `PyYAML`: YAML frontmatter

## See Also

- [Export System API](../core/exporters.py)
- [Notion Exporter](../exporters/notion_exporter.py)
- [Confluence Exporter](../exporters/confluence_exporter.py)
- [WordPress Exporter](../exporters/wordpress_exporter.py)
- [Medium Exporter](../exporters/medium_exporter.py)
- [GitHub Wiki Exporter](../exporters/github_wiki_exporter.py)
- [Obsidian Exporter](../exporters/obsidian_exporter.py)
- [Export UI](../components/export_ui.py)
- [Export Window](../views/export_window.py)

