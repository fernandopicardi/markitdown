"""
Template management window for MarkItDown GUI.

This module provides a complete UI for managing templates,
editing templates, and previewing results.
"""

import customtkinter as ctk
from tkinter import messagebox
from pathlib import Path
from typing import Optional, Dict, Any
import logging

from gui.core.templates import TemplateManager, MarkdownTemplate, TemplateCategory
from gui.components.template_editor import TemplateEditor, TemplateManagerUI

logger = logging.getLogger(__name__)


class TemplateManagementWindow(ctk.CTk):
    """Main window for template management."""

    def __init__(self, storage_path: Optional[Path] = None, **kwargs) -> None:
        """
        Initialize template management window.
        
        Args:
            storage_path: Path to store templates
            **kwargs: Additional CTk arguments
        """
        super().__init__(**kwargs)
        self.template_manager = TemplateManager(storage_path=storage_path)
        self.current_template: Optional[MarkdownTemplate] = None

        self._setup_window()
        self._create_layout()

        logger.info("Template management window initialized")

    def _setup_window(self) -> None:
        """Configure window properties."""
        self.title("MarkItDown - Template Management")
        self.geometry("1400x900")
        self.minsize(1200, 700)

    def _create_layout(self) -> None:
        """Create main layout."""
        # Top bar
        top_bar = ctk.CTkFrame(self)
        top_bar.pack(fill="x", padx=10, pady=10)

        ctk.CTkLabel(
            top_bar,
            text="Template System",
            font=ctk.CTkFont(size=20, weight="bold"),
        ).pack(side="left", padx=10)

        # Main content area
        main_frame = ctk.CTkFrame(self)
        main_frame.pack(fill="both", expand=True, padx=10, pady=10)

        # Left side - Template library
        left_frame = ctk.CTkFrame(main_frame)
        left_frame.pack(side="left", fill="both", expand=False, padx=5)

        self.template_manager_ui = TemplateManagerUI(
            left_frame,
            self.template_manager,
            on_template_selected=self._on_template_selected,
        )
        self.template_manager_ui.pack(fill="both", expand=True)

        # Right side - Editor/Preview
        right_frame = ctk.CTkFrame(main_frame)
        right_frame.pack(side="right", fill="both", expand=True, padx=5)

        # Tab view for editor and preview
        self.tabs = ctk.CTkTabview(right_frame)
        self.tabs.pack(fill="both", expand=True)

        # Editor tab
        editor_tab = self.tabs.add("Editor")
        self.template_editor = TemplateEditor(
            editor_tab,
            template=None,
            on_save=self._save_template,
            on_preview=self._update_preview,
        )
        self.template_editor.pack(fill="both", expand=True)

        # Preview tab
        preview_tab = self.tabs.add("Preview")
        self.preview_frame = ctk.CTkFrame(preview_tab)
        self.preview_frame.pack(fill="both", expand=True, padx=10, pady=10)

        ctk.CTkLabel(
            self.preview_frame,
            text="Rendered Output Preview",
            font=ctk.CTkFont(size=14, weight="bold"),
        ).pack(pady=5)

        self.preview_output = ctk.CTkTextbox(
            self.preview_frame,
            wrap="word",
            font=ctk.CTkFont(family="Consolas", size=10),
        )
        self.preview_output.pack(fill="both", expand=True)

        # Library tab
        library_tab = self.tabs.add("Library")
        self._create_library_view(library_tab)

    def _create_library_view(self, parent: ctk.CTkFrame) -> None:
        """Create library view with predefined templates."""
        # Categories
        categories_frame = ctk.CTkFrame(parent)
        categories_frame.pack(fill="x", padx=10, pady=10)

        ctk.CTkLabel(
            categories_frame,
            text="Template Categories",
            font=ctk.CTkFont(size=14, weight="bold"),
        ).pack(pady=5)

        # Category buttons
        button_frame = ctk.CTkFrame(categories_frame)
        button_frame.pack(fill="x", padx=10, pady=5)

        categories = [
            ("Technical", TemplateCategory.TECHNICAL),
            ("Blog", TemplateCategory.BLOG),
            ("Academic", TemplateCategory.ACADEMIC),
            ("Minimalist", TemplateCategory.MINIMALIST),
        ]

        for name, category in categories:
            btn = ctk.CTkButton(
                button_frame,
                text=name,
                command=lambda c=category: self._load_category_templates(c),
                width=120,
            )
            btn.pack(side="left", padx=5)

        # Templates list
        list_frame = ctk.CTkFrame(parent)
        list_frame.pack(fill="both", expand=True, padx=10, pady=10)

        self.library_listbox = ctk.CTkTextbox(list_frame)
        self.library_listbox.pack(fill="both", expand=True)

        # Load all templates
        self._load_all_templates()

    def _load_all_templates(self) -> None:
        """Load all templates into library view."""
        templates = self.template_manager.get_all_templates()
        self.library_listbox.delete("1.0", "end")

        for template in templates:
            self.library_listbox.insert(
                "end",
                f"📄 {template.name}\n"
                f"   Category: {template.category.value}\n"
                f"   {template.description}\n"
                f"   ID: {template.template_id}\n\n"
            )

    def _load_category_templates(self, category: TemplateCategory) -> None:
        """Load templates by category."""
        templates = self.template_manager.get_templates_by_category(category)
        self.library_listbox.delete("1.0", "end")

        if not templates:
            self.library_listbox.insert("1.0", f"No templates found in category: {category.value}")
            return

        for template in templates:
            self.library_listbox.insert(
                "end",
                f"📄 {template.name}\n"
                f"   {template.description}\n"
                f"   ID: {template.template_id}\n\n"
            )

    def _on_template_selected(self, template_id: str) -> None:
        """Handle template selection."""
        template = self.template_manager.get_template(template_id)
        if template:
            self.current_template = template
            self.template_editor.template = template
            self.template_editor._load_template()
            self._update_preview()

    def _save_template(self, template: MarkdownTemplate) -> None:
        """Save template."""
        try:
            self.template_manager.add_template(template)
            messagebox.showinfo("Success", f"Template '{template.name}' saved successfully!")
            self._load_all_templates()
        except Exception as e:
            logger.error(f"Failed to save template: {e}")
            messagebox.showerror("Error", f"Failed to save template: {e}")

    def _update_preview(self, rendered_text: Optional[str] = None) -> None:
        """Update preview output."""
        if rendered_text:
            self.preview_output.delete("1.0", "end")
            self.preview_output.insert("1.0", rendered_text)
        else:
            # Generate preview from current template
            if self.current_template:
                sample_content = """# Sample Content

This is a sample markdown content for preview.

## Section 1

Some text here with **bold** and *italic* formatting.

### Subsection

- List item 1
- List item 2
- List item 3

## Section 2

More content with `code` and [links](https://example.com).
"""

                try:
                    rendered = self.current_template.render(
                        sample_content,
                        metadata={
                            "title": "Preview Document",
                            "author": "Preview Author",
                            "date": "2024-01-01",
                        }
                    )
                    self.preview_output.delete("1.0", "end")
                    self.preview_output.insert("1.0", rendered)
                except Exception as e:
                    self.preview_output.delete("1.0", "end")
                    self.preview_output.insert("1.0", f"Preview Error: {e}")

    def apply_template(self, content: str, template_id: Optional[str] = None, metadata: Optional[Dict[str, Any]] = None) -> str:
        """
        Apply template to content.
        
        Args:
            content: Content to apply template to
            template_id: Template ID (uses default if None)
            metadata: Optional metadata
            
        Returns:
            Rendered content
        """
        if template_id:
            template = self.template_manager.get_template(template_id)
        else:
            template = self.template_manager.get_default_template()

        if not template:
            return content

        return template.render(content, metadata=metadata)

    def run(self) -> None:
        """Start the window."""
        logger.info("Starting template management window")
        self.mainloop()


class TemplateSelectorDialog(ctk.CTkToplevel):
    """Dialog for selecting a template."""

    def __init__(self, parent: Any, template_manager: TemplateManager, **kwargs) -> None:
        """
        Initialize template selector dialog.
        
        Args:
            parent: Parent window
            template_manager: TemplateManager instance
            **kwargs: Additional CTkToplevel arguments
        """
        super().__init__(parent, **kwargs)
        self.template_manager = template_manager
        self.selected_template: Optional[MarkdownTemplate] = None

        self.title("Select Template")
        self.geometry("600x500")

        self._create_widgets()

    def _create_widgets(self) -> None:
        """Create dialog widgets."""
        # Header
        header = ctk.CTkFrame(self)
        header.pack(fill="x", padx=10, pady=10)

        ctk.CTkLabel(
            header,
            text="Select Template",
            font=ctk.CTkFont(size=16, weight="bold"),
        ).pack()

        # Template list
        list_frame = ctk.CTkFrame(self)
        list_frame.pack(fill="both", expand=True, padx=10, pady=10)

        self.template_listbox = ctk.CTkTextbox(list_frame)
        self.template_listbox.pack(fill="both", expand=True)

        # Load templates
        templates = self.template_manager.get_all_templates()
        for template in templates:
            self.template_listbox.insert(
                "end",
                f"📄 {template.name} ({template.category.value})\n"
                f"   {template.description}\n\n"
            )

        # Buttons
        button_frame = ctk.CTkFrame(self)
        button_frame.pack(fill="x", padx=10, pady=10)

        ctk.CTkButton(
            button_frame,
            text="Cancel",
            command=self._cancel,
            width=100,
        ).pack(side="right", padx=5)

        ctk.CTkButton(
            button_frame,
            text="Select",
            command=self._select,
            width=100,
        ).pack(side="right", padx=5)

    def _select(self) -> None:
        """Select template."""
        # Simplified: select first template
        templates = self.template_manager.get_all_templates()
        if templates:
            self.selected_template = templates[0]
        self.destroy()

    def _cancel(self) -> None:
        """Cancel selection."""
        self.selected_template = None
        self.destroy()

    def get_selected_template(self) -> Optional[MarkdownTemplate]:
        """Get selected template."""
        return self.selected_template

