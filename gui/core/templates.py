"""
Template and post-processing system for MarkItDown GUI.

This module provides Jinja2-based templates and configurable
post-processing for customizing Markdown output.
"""

import re
import logging
from pathlib import Path
from typing import Dict, List, Optional, Any, Callable
from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum
import json

try:
    from jinja2 import Template, Environment, FileSystemLoader, select_autoescape
    from jinja2.exceptions import TemplateError, TemplateSyntaxError
except ImportError:
    Template = None
    Environment = None
    TemplateError = Exception
    TemplateSyntaxError = Exception

logger = logging.getLogger(__name__)


class TemplateCategory(Enum):
    """Template categories."""

    TECHNICAL = "technical"
    BLOG = "blog"
    ACADEMIC = "academic"
    MINIMALIST = "minimalist"
    CUSTOM = "custom"


@dataclass
class PostProcessingRule:
    """A single post-processing rule."""

    name: str
    enabled: bool = True
    rule_type: str = "text_replacement"  # text_replacement, regex, cleanup, etc.
    pattern: Optional[str] = None
    replacement: Optional[str] = None
    options: Dict[str, Any] = field(default_factory=dict)

    def apply(self, text: str) -> str:
        """
        Apply this rule to text.
        
        Args:
            text: Input text
            
        Returns:
            Processed text
        """
        if not self.enabled:
            return text

        try:
            if self.rule_type == "text_replacement":
                if self.pattern and self.replacement:
                    return text.replace(self.pattern, self.replacement)
            elif self.rule_type == "regex_replacement":
                if self.pattern and self.replacement:
                    return re.sub(self.pattern, self.replacement, text, flags=re.MULTILINE)
            elif self.rule_type == "remove_whitespace":
                # Remove excessive whitespace
                text = re.sub(r'\n{3,}', '\n\n', text)  # Max 2 newlines
                text = re.sub(r'[ \t]+', ' ', text)  # Multiple spaces to one
                return text.strip()
            elif self.rule_type == "normalize_links":
                # Normalize markdown links
                # Convert [text](url) to consistent format
                return text  # Placeholder
            elif self.rule_type == "remove_elements":
                # Remove specific markdown elements
                if self.pattern:
                    # Remove matching elements
                    text = re.sub(self.pattern, '', text, flags=re.MULTILINE)
                return text
            elif self.rule_type == "format_dates":
                # Convert date formats
                # This would need date parsing logic
                return text
            elif self.rule_type == "optimize_images":
                # Image optimization placeholder
                return text
        except Exception as e:
            logger.error(f"Error applying rule {self.name}: {e}")
            return text

        return text


@dataclass
class PostProcessingPipeline:
    """Post-processing pipeline with multiple rules."""

    name: str
    rules: List[PostProcessingRule] = field(default_factory=list)
    enabled: bool = True

    def apply(self, text: str) -> str:
        """
        Apply all rules in pipeline to text.
        
        Args:
            text: Input text
            
        Returns:
            Processed text
        """
        if not self.enabled:
            return text

        result = text
        for rule in self.rules:
            result = rule.apply(result)
        return result

    def add_rule(self, rule: PostProcessingRule) -> None:
        """Add a rule to the pipeline."""
        self.rules.append(rule)

    def remove_rule(self, rule_name: str) -> bool:
        """Remove a rule from the pipeline."""
        for i, rule in enumerate(self.rules):
            if rule.name == rule_name:
                self.rules.pop(i)
                return True
        return False


@dataclass
class MarkdownTemplate:
    """Markdown template with Jinja2."""

    template_id: str
    name: str
    category: TemplateCategory
    description: str = ""
    template_content: str = ""
    header_template: str = ""
    footer_template: str = ""
    metadata: Dict[str, Any] = field(default_factory=dict)
    post_processing: Optional[PostProcessingPipeline] = None
    created_at: datetime = field(default_factory=datetime.now)
    updated_at: datetime = field(default_factory=datetime.now)

    def render(
        self,
        content: str,
        metadata: Optional[Dict[str, Any]] = None,
        **kwargs: Any
    ) -> str:
        """
        Render template with content.
        
        Args:
            content: Main content to render
            metadata: Optional metadata to merge
            **kwargs: Additional template variables
            
        Returns:
            Rendered markdown
        """
        if Template is None:
            logger.error("Jinja2 not available")
            return content

        try:
            # Merge metadata
            template_vars = {
                "content": content,
                "metadata": {**self.metadata, **(metadata or {})},
                "date": datetime.now().strftime("%Y-%m-%d"),
                "time": datetime.now().strftime("%H:%M:%S"),
                **kwargs,
            }

            # Render header
            header = ""
            if self.header_template:
                header_template = Template(self.header_template)
                header = header_template.render(**template_vars)

            # Render main content
            if self.template_content:
                main_template = Template(self.template_content)
                rendered_content = main_template.render(**template_vars)
            else:
                rendered_content = content

            # Render footer
            footer = ""
            if self.footer_template:
                footer_template = Template(self.footer_template)
                footer = footer_template.render(**template_vars)

            # Combine
            result = "\n\n".join(filter(None, [header, rendered_content, footer]))

            # Apply post-processing
            if self.post_processing:
                result = self.post_processing.apply(result)

            return result

        except TemplateError as e:
            logger.error(f"Template rendering error: {e}")
            return content
        except Exception as e:
            logger.error(f"Error rendering template: {e}")
            return content

    def validate(self) -> tuple:
        """
        Validate template syntax.
        
        Returns:
            Tuple of (is_valid, error_message)
        """
        if Template is None:
            return False, "Jinja2 not available"

        errors = []

        # Validate header
        if self.header_template:
            try:
                Template(self.header_template)
            except TemplateSyntaxError as e:
                errors.append(f"Header template error: {e}")

        # Validate main template
        if self.template_content:
            try:
                Template(self.template_content)
            except TemplateSyntaxError as e:
                errors.append(f"Main template error: {e}")

        # Validate footer
        if self.footer_template:
            try:
                Template(self.footer_template)
            except TemplateSyntaxError as e:
                errors.append(f"Footer template error: {e}")

        if errors:
            return False, "; ".join(errors)

        return True, None

    def to_dict(self) -> Dict[str, Any]:
        """Convert template to dictionary."""
        return {
            "template_id": self.template_id,
            "name": self.name,
            "category": self.category.value,
            "description": self.description,
            "template_content": self.template_content,
            "header_template": self.header_template,
            "footer_template": self.footer_template,
            "metadata": self.metadata,
            "post_processing": {
                "name": self.post_processing.name if self.post_processing else None,
                "enabled": self.post_processing.enabled if self.post_processing else False,
                "rules": [
                    {
                        "name": r.name,
                        "enabled": r.enabled,
                        "rule_type": r.rule_type,
                        "pattern": r.pattern,
                        "replacement": r.replacement,
                        "options": r.options,
                    }
                    for r in (self.post_processing.rules if self.post_processing else [])
                ],
            } if self.post_processing else None,
            "created_at": self.created_at.isoformat(),
            "updated_at": self.updated_at.isoformat(),
        }

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "MarkdownTemplate":
        """Create template from dictionary."""
        # Reconstruct post-processing
        post_processing = None
        if data.get("post_processing"):
            pp_data = data["post_processing"]
            rules = [
                PostProcessingRule(
                    name=r["name"],
                    enabled=r.get("enabled", True),
                    rule_type=r.get("rule_type", "text_replacement"),
                    pattern=r.get("pattern"),
                    replacement=r.get("replacement"),
                    options=r.get("options", {}),
                )
                for r in pp_data.get("rules", [])
            ]
            post_processing = PostProcessingPipeline(
                name=pp_data.get("name", "default"),
                rules=rules,
                enabled=pp_data.get("enabled", True),
            )

        return cls(
            template_id=data.get("template_id", ""),
            name=data.get("name", "Untitled"),
            category=TemplateCategory(data.get("category", "custom")),
            description=data.get("description", ""),
            template_content=data.get("template_content", ""),
            header_template=data.get("header_template", ""),
            footer_template=data.get("footer_template", ""),
            metadata=data.get("metadata", {}),
            post_processing=post_processing,
            created_at=datetime.fromisoformat(data.get("created_at", datetime.now().isoformat())),
            updated_at=datetime.fromisoformat(data.get("updated_at", datetime.now().isoformat())),
        )


class TemplateManager:
    """Manages markdown templates."""

    def __init__(self, storage_path: Optional[Path] = None) -> None:
        """
        Initialize template manager.
        
        Args:
            storage_path: Path to store templates (defaults to user config)
        """
        if storage_path is None:
            import os
            if os.name == "nt":  # Windows
                storage_path = Path.home() / "AppData" / "Local" / "MarkItDown" / "templates"
            else:  # Linux/Mac
                storage_path = Path.home() / ".config" / "markitdown" / "templates"
            storage_path.mkdir(parents=True, exist_ok=True)

        self.storage_path = storage_path
        self.templates: Dict[str, MarkdownTemplate] = {}
        self.default_template_id: Optional[str] = None

        # Load templates
        self._load_templates()
        self._create_default_templates()

    def _load_templates(self) -> None:
        """Load templates from storage."""
        if not self.storage_path.exists():
            return

        for template_file in self.storage_path.glob("*.json"):
            try:
                with open(template_file, "r", encoding="utf-8") as f:
                    data = json.load(f)
                template = MarkdownTemplate.from_dict(data)
                self.templates[template.template_id] = template
            except Exception as e:
                logger.error(f"Failed to load template {template_file}: {e}")

    def _create_default_templates(self) -> None:
        """Create default templates if they don't exist."""
        defaults = self._get_default_templates()
        for template in defaults:
            if template.template_id not in self.templates:
                self.templates[template.template_id] = template
                self.save_template(template)

    def _get_default_templates(self) -> List[MarkdownTemplate]:
        """Get default template definitions."""
        templates = []

        # Technical/Documentation Template
        technical = MarkdownTemplate(
            template_id="technical_default",
            name="Technical Documentation",
            category=TemplateCategory.TECHNICAL,
            description="Template for technical documentation with TOC and code formatting",
            header_template="""# {{ metadata.get('title', 'Documentation') }}

{% if metadata.get('author') %}
**Author:** {{ metadata.author }}  
{% endif %}
{% if metadata.get('version') %}
**Version:** {{ metadata.version }}  
{% endif %}
**Date:** {{ date }}

{% if metadata.get('tags') %}
**Tags:** {{ metadata.tags | join(', ') }}
{% endif %}

---

## Table of Contents
[TOC will be generated here]

---

""",
            template_content="{{ content }}",
            footer_template="""
---

**Generated:** {{ date }} {{ time }}
""",
            metadata={"title": "Documentation", "version": "1.0"},
        )
        templates.append(technical)

        # Blog/Article Template
        blog = MarkdownTemplate(
            template_id="blog_default",
            name="Blog Article",
            category=TemplateCategory.BLOG,
            description="Template for blog posts and articles",
            header_template="""---
title: {{ metadata.get('title', 'Article') }}
author: {{ metadata.get('author', 'Unknown') }}
date: {{ date }}
tags: {{ metadata.get('tags', []) | join(', ') }}
---

# {{ metadata.get('title', 'Article') }}

*By {{ metadata.get('author', 'Unknown') }} on {{ date }}*

---

""",
            template_content="{{ content }}",
            footer_template="""
---

*Published on {{ date }}*
""",
        )
        templates.append(blog)

        # Academic Template
        academic = MarkdownTemplate(
            template_id="academic_default",
            name="Academic Paper",
            category=TemplateCategory.ACADEMIC,
            description="Template for academic papers and research documents",
            header_template="""# {{ metadata.get('title', 'Paper Title') }}

{% if metadata.get('authors') %}
**Authors:** {{ metadata.authors | join(', ') }}  
{% endif %}
{% if metadata.get('institution') %}
**Institution:** {{ metadata.institution }}  
{% endif %}
{% if metadata.get('date') %}
**Date:** {{ metadata.date }}  
{% else %}
**Date:** {{ date }}
{% endif %}

## Abstract

{% if metadata.get('abstract') %}
{{ metadata.abstract }}
{% else %}
[Abstract will be added here]
{% endif %}

---

## 1. Introduction

""",
            template_content="{{ content }}",
            footer_template="""
---

## References

{% if metadata.get('references') %}
{% for ref in metadata.references %}
- {{ ref }}
{% endfor %}
{% else %}
[References will be added here]
{% endif %}

---
*Document generated on {{ date }}*
""",
        )
        templates.append(academic)

        # Minimalist Template
        minimalist = MarkdownTemplate(
            template_id="minimalist_default",
            name="Minimalist",
            category=TemplateCategory.MINIMALIST,
            description="Simple, clean template with minimal formatting",
            header_template="""# {{ metadata.get('title', 'Document') }}

""",
            template_content="{{ content }}",
            footer_template="",
        )
        templates.append(minimalist)

        return templates

    def get_template(self, template_id: str) -> Optional[MarkdownTemplate]:
        """
        Get template by ID.
        
        Args:
            template_id: Template ID
            
        Returns:
            Template or None
        """
        return self.templates.get(template_id)

    def get_templates_by_category(self, category: TemplateCategory) -> List[MarkdownTemplate]:
        """
        Get templates by category.
        
        Args:
            category: Template category
            
        Returns:
            List of templates
        """
        return [t for t in self.templates.values() if t.category == category]

    def add_template(self, template: MarkdownTemplate) -> None:
        """
        Add or update template.
        
        Args:
            template: Template to add/update
        """
        template.updated_at = datetime.now()
        self.templates[template.template_id] = template
        self.save_template(template)
        logger.info(f"Template added/updated: {template.name}")

    def remove_template(self, template_id: str) -> bool:
        """
        Remove template.
        
        Args:
            template_id: Template ID to remove
            
        Returns:
            True if removed, False if not found
        """
        if template_id in self.templates:
            template = self.templates[template_id]
            # Don't allow removing default templates
            if template.template_id.startswith("_default"):
                logger.warning(f"Cannot remove default template: {template_id}")
                return False

            del self.templates[template_id]
            # Delete file
            template_file = self.storage_path / f"{template_id}.json"
            if template_file.exists():
                template_file.unlink()
            logger.info(f"Template removed: {template_id}")
            return True
        return False

    def save_template(self, template: MarkdownTemplate) -> None:
        """
        Save template to disk.
        
        Args:
            template: Template to save
        """
        template_file = self.storage_path / f"{template.template_id}.json"
        try:
            with open(template_file, "w", encoding="utf-8") as f:
                json.dump(template.to_dict(), f, indent=2, ensure_ascii=False)
        except Exception as e:
            logger.error(f"Failed to save template {template.template_id}: {e}")

    def export_template(self, template_id: str, export_path: Path) -> bool:
        """
        Export template to file.
        
        Args:
            template_id: Template ID to export
            export_path: Path to export file
            
        Returns:
            True if exported, False if not found
        """
        template = self.templates.get(template_id)
        if not template:
            return False

        try:
            with open(export_path, "w", encoding="utf-8") as f:
                json.dump(template.to_dict(), f, indent=2, ensure_ascii=False)
            return True
        except Exception as e:
            logger.error(f"Failed to export template: {e}")
            return False

    def import_template(self, import_path: Path) -> Optional[MarkdownTemplate]:
        """
        Import template from file.
        
        Args:
            import_path: Path to import file
            
        Returns:
            Imported template or None
        """
        try:
            with open(import_path, "r", encoding="utf-8") as f:
                data = json.load(f)
            template = MarkdownTemplate.from_dict(data)
            # Generate new ID if importing
            if template.template_id in self.templates:
                template.template_id = f"imported_{int(datetime.now().timestamp())}"
            self.add_template(template)
            return template
        except Exception as e:
            logger.error(f"Failed to import template: {e}")
            return None

    def get_all_templates(self) -> List[MarkdownTemplate]:
        """
        Get all templates.
        
        Returns:
            List of all templates
        """
        return list(self.templates.values())

    def set_default_template(self, template_id: str) -> bool:
        """
        Set default template.
        
        Args:
            template_id: Template ID to set as default
            
        Returns:
            True if set, False if not found
        """
        if template_id in self.templates:
            self.default_template_id = template_id
            return True
        return False

    def get_default_template(self) -> Optional[MarkdownTemplate]:
        """
        Get default template.
        
        Returns:
            Default template or None
        """
        if self.default_template_id:
            return self.templates.get(self.default_template_id)
        return None

