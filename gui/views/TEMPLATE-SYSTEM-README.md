# Template and Post-Processing System

## Overview

The MarkItDown GUI features a comprehensive template and post-processing system that allows you to customize Markdown output using Jinja2 templates and configurable post-processing rules.

## Features

### ✅ Jinja2 Templates
- **Header/Footer**: Custom headers and footers
- **Metadata**: Author, date, tags, version
- **Automatic TOC**: Table of contents generation
- **Code Formatting**: Syntax highlighting support
- **Table Styles**: Custom table formatting
- **Variables**: Dynamic content insertion

### ✅ Post-Processing Pipeline
- **Text Replacement**: Simple text substitutions
- **Regex Replacement**: Pattern-based replacements
- **Whitespace Cleanup**: Remove excessive whitespace
- **Link Normalization**: Standardize link formats
- **Element Removal**: Remove specific markdown elements
- **Date Formatting**: Convert date formats
- **Image Optimization**: Image processing (placeholder)

### ✅ Template Library
- **Technical/Documentation**: For technical docs
- **Blog/Article**: For blog posts
- **Academic**: For academic papers
- **Minimalist**: Simple, clean template
- **Custom**: User-defined templates

### ✅ Template Editor
- **Visual Editor**: Edit templates with syntax highlighting
- **Real-time Preview**: See changes instantly
- **Validation**: Syntax validation
- **Tabs**: Separate sections for header, content, footer
- **Post-Processing UI**: Manage post-processing rules

### ✅ Import/Export
- **Export Templates**: Save templates as JSON
- **Import Templates**: Load templates from files
- **Share Templates**: Easy template sharing

### ✅ Validation
- **Syntax Checking**: Validate Jinja2 syntax
- **Error Messages**: Clear error reporting
- **Template Testing**: Test before saving

## Usage

### Basic Template Usage

```python
from gui.core.templates import TemplateManager, MarkdownTemplate

# Create template manager
manager = TemplateManager()

# Get template
template = manager.get_template("technical_default")

# Render content
rendered = template.render(
    content="# My Content\n\nSome text here.",
    metadata={
        "title": "My Document",
        "author": "John Doe",
        "version": "1.0"
    }
)
```

### Creating Custom Templates

```python
from gui.core.templates import MarkdownTemplate, TemplateCategory

template = MarkdownTemplate(
    template_id="my_template",
    name="My Custom Template",
    category=TemplateCategory.CUSTOM,
    description="A custom template",
    header_template="""# {{ metadata.get('title', 'Document') }}

Author: {{ metadata.get('author', 'Unknown') }}
Date: {{ date }}

---

""",
    template_content="{{ content }}",
    footer_template="""
---

Generated on {{ date }}
""",
)

# Add to manager
manager.add_template(template)
```

### Post-Processing Rules

```python
from gui.core.templates import PostProcessingRule, PostProcessingPipeline

# Create pipeline
pipeline = PostProcessingPipeline(name="cleanup")

# Add rules
pipeline.add_rule(PostProcessingRule(
    name="remove_whitespace",
    rule_type="remove_whitespace",
    enabled=True,
))

pipeline.add_rule(PostProcessingRule(
    name="replace_text",
    rule_type="text_replacement",
    pattern="old text",
    replacement="new text",
))

# Apply to template
template.post_processing = pipeline
```

### Using Templates in Conversion

```python
from gui.views.template_window import TemplateManagementWindow

# Create window
window = TemplateManagementWindow()

# Apply template to content
rendered = window.apply_template(
    content=markdown_content,
    template_id="technical_default",
    metadata={"title": "My Doc", "author": "Me"}
)
```

## Template Syntax

### Jinja2 Variables

```jinja2
{{ variable_name }}
{{ metadata.get('key', 'default') }}
{{ date }}
{{ time }}
```

### Jinja2 Control Structures

```jinja2
{% if condition %}
    Content
{% endif %}

{% for item in list %}
    {{ item }}
{% endfor %}
```

### Example Template

```jinja2
# {{ metadata.get('title', 'Document') }}

{% if metadata.get('author') %}
**Author:** {{ metadata.author }}
{% endif %}

**Date:** {{ date }}

---

{{ content }}

---

*Generated on {{ date }} at {{ time }}*
```

## Post-Processing Rules

### Rule Types

1. **text_replacement**: Simple text replacement
   ```python
   PostProcessingRule(
       name="replace",
       rule_type="text_replacement",
       pattern="old",
       replacement="new"
   )
   ```

2. **regex_replacement**: Regex-based replacement
   ```python
   PostProcessingRule(
       name="regex_replace",
       rule_type="regex_replacement",
       pattern=r'\d+',
       replacement="NUMBER"
   )
   ```

3. **remove_whitespace**: Clean up whitespace
   ```python
   PostProcessingRule(
       name="cleanup",
       rule_type="remove_whitespace"
   )
   ```

4. **normalize_links**: Normalize markdown links
   ```python
   PostProcessingRule(
       name="normalize",
       rule_type="normalize_links"
   )
   ```

5. **remove_elements**: Remove specific elements
   ```python
   PostProcessingRule(
       name="remove",
       rule_type="remove_elements",
       pattern=r'<!--.*?-->'  # Remove HTML comments
   )
   ```

6. **format_dates**: Convert date formats
   ```python
   PostProcessingRule(
       name="format_dates",
       rule_type="format_dates"
   )
   ```

7. **optimize_images**: Image optimization
   ```python
   PostProcessingRule(
       name="optimize",
       rule_type="optimize_images"
   )
   ```

## Predefined Templates

### Technical Documentation

```jinja2
# {{ metadata.get('title', 'Documentation') }}

**Author:** {{ metadata.author }}
**Version:** {{ metadata.version }}
**Date:** {{ date }}

## Table of Contents
[TOC]

---

{{ content }}

---

**Generated:** {{ date }} {{ time }}
```

### Blog Article

```jinja2
---
title: {{ metadata.get('title', 'Article') }}
author: {{ metadata.get('author', 'Unknown') }}
date: {{ date }}
tags: {{ metadata.get('tags', []) | join(', ') }}
---

# {{ metadata.get('title', 'Article') }}

*By {{ metadata.get('author', 'Unknown') }} on {{ date }}*

---

{{ content }}

---

*Published on {{ date }}*
```

### Academic Paper

```jinja2
# {{ metadata.get('title', 'Paper Title') }}

**Authors:** {{ metadata.authors | join(', ') }}
**Institution:** {{ metadata.institution }}
**Date:** {{ date }}

## Abstract

{{ metadata.abstract }}

---

{{ content }}

---

## References

{% for ref in metadata.references %}
- {{ ref }}
{% endfor %}
```

### Minimalist

```jinja2
# {{ metadata.get('title', 'Document') }}

{{ content }}
```

## Template Editor

### Features

- **Syntax Highlighting**: Jinja2 syntax highlighting
- **Real-time Preview**: See changes as you type
- **Validation**: Check syntax before saving
- **Tabs**: Separate sections for header, content, footer
- **Post-Processing**: Manage post-processing rules
- **Save/Load**: Save and load templates

### Usage

```python
from gui.views.template_window import TemplateManagementWindow

window = TemplateManagementWindow()
window.run()
```

## Import/Export

### Export Template

```python
# Export to file
manager.export_template(
    template_id="my_template",
    export_path=Path("template.json")
)
```

### Import Template

```python
# Import from file
template = manager.import_template(
    import_path=Path("template.json")
)
```

## Integration

### With Conversion System

```python
from gui.models.conversion_model import ConversionModel
from gui.core.templates import TemplateManager

# Convert file
model = ConversionModel(event_bus)
result = model.convert(input_file)

# Apply template
template_manager = TemplateManager()
template = template_manager.get_template("technical_default")
rendered = template.render(
    result.result_text,
    metadata={"title": "Converted Document"}
)
```

### With Batch Processing

```python
# Apply template in batch processing
for task in batch_tasks:
    result = process_task(task)
    rendered = template.render(result.content)
    save_output(rendered)
```

## Best Practices

1. **Use Metadata**: Leverage metadata for dynamic content
2. **Test Templates**: Always preview before using
3. **Validate**: Check syntax before saving
4. **Organize**: Use categories to organize templates
5. **Post-Process**: Use post-processing for cleanup
6. **Version Control**: Export templates for version control
7. **Document**: Add descriptions to templates

## Troubleshooting

### Template Not Rendering

- Check Jinja2 syntax
- Verify variables are defined
- Check template validation

### Post-Processing Not Working

- Ensure rules are enabled
- Check rule patterns
- Verify rule order

### Import/Export Issues

- Check file permissions
- Verify JSON format
- Check template structure

## See Also

- [Jinja2 Documentation](https://jinja.palletsprojects.com/)
- [Template Manager API](../core/templates.py)
- [Template Editor](../components/template_editor.py)
- [Template Window](../views/template_window.py)

