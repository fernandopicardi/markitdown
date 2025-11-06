"""
Template editor component with real-time preview.
"""

import customtkinter as ctk
from typing import Optional, Callable, Dict, Any
import logging

from pathlib import Path
from gui.core.templates import MarkdownTemplate, PostProcessingRule, PostProcessingPipeline

logger = logging.getLogger(__name__)


class TemplateEditor(ctk.CTkFrame):
    """Template editor with syntax highlighting and preview."""

    def __init__(
        self,
        master: Any,
        template: Optional[MarkdownTemplate] = None,
        on_save: Optional[Callable[[MarkdownTemplate], None]] = None,
        on_preview: Optional[Callable[[str], None]] = None,
        **kwargs
    ) -> None:
        """
        Initialize template editor.
        
        Args:
            master: Parent widget
            template: Template to edit (None for new)
            on_save: Callback when template is saved
            on_preview: Callback for preview updates
            **kwargs: Additional CTkFrame arguments
        """
        super().__init__(master, **kwargs)
        self.template = template or self._create_new_template()
        self.on_save = on_save
        self.on_preview = on_preview

        self._create_widgets()
        self._load_template()

    def _create_new_template(self) -> MarkdownTemplate:
        """Create a new empty template."""
        from gui.core.templates import TemplateCategory
        return MarkdownTemplate(
            template_id="new_template",
            name="New Template",
            category=TemplateCategory.CUSTOM,
        )

    def _create_widgets(self) -> None:
        """Create editor widgets."""
        # Top toolbar
        toolbar = ctk.CTkFrame(self)
        toolbar.pack(fill="x", padx=5, pady=5)

        ctk.CTkLabel(
            toolbar,
            text="Template Editor",
            font=ctk.CTkFont(size=16, weight="bold"),
        ).pack(side="left", padx=10)

        self.validate_button = ctk.CTkButton(
            toolbar,
            text="Validate",
            command=self._validate_template,
            width=100,
        )
        self.validate_button.pack(side="right", padx=5)

        self.preview_button = ctk.CTkButton(
            toolbar,
            text="Preview",
            command=self._update_preview,
            width=100,
        )
        self.preview_button.pack(side="right", padx=5)

        self.save_button = ctk.CTkButton(
            toolbar,
            text="Save",
            command=self._save_template,
            width=100,
        )
        self.save_button.pack(side="right", padx=5)

        # Main content area
        content_frame = ctk.CTkFrame(self)
        content_frame.pack(fill="both", expand=True, padx=5, pady=5)

        # Left side - Editor
        editor_frame = ctk.CTkFrame(content_frame)
        editor_frame.pack(side="left", fill="both", expand=True, padx=5)

        # Template name
        name_frame = ctk.CTkFrame(editor_frame)
        name_frame.pack(fill="x", padx=5, pady=5)

        ctk.CTkLabel(name_frame, text="Name:").pack(side="left", padx=5)
        self.name_var = ctk.StringVar(value=self.template.name)
        name_entry = ctk.CTkEntry(name_frame, textvariable=self.name_var, width=200)
        name_entry.pack(side="left", padx=5)

        # Tab view for different template parts
        self.template_tabs = ctk.CTkTabview(editor_frame)
        self.template_tabs.pack(fill="both", expand=True, padx=5, pady=5)

        # Header tab
        header_tab = self.template_tabs.add("Header")
        self.header_text = ctk.CTkTextbox(
            header_tab,
            wrap="none",
            font=ctk.CTkFont(family="Consolas", size=11),
        )
        self.header_text.pack(fill="both", expand=True, padx=5, pady=5)

        # Content tab
        content_tab = self.template_tabs.add("Content")
        self.content_text = ctk.CTkTextbox(
            content_tab,
            wrap="none",
            font=ctk.CTkFont(family="Consolas", size=11),
        )
        self.content_text.pack(fill="both", expand=True, padx=5, pady=5)

        # Footer tab
        footer_tab = self.template_tabs.add("Footer")
        self.footer_text = ctk.CTkTextbox(
            footer_tab,
            wrap="none",
            font=ctk.CTkFont(family="Consolas", size=11),
        )
        self.footer_text.pack(fill="both", expand=True, padx=5, pady=5)

        # Post-processing tab
        pp_tab = self.template_tabs.add("Post-Processing")
        self._create_post_processing_ui(pp_tab)

        # Right side - Preview
        preview_frame = ctk.CTkFrame(content_frame)
        preview_frame.pack(side="right", fill="both", expand=True, padx=5)

        ctk.CTkLabel(
            preview_frame,
            text="Preview",
            font=ctk.CTkFont(size=14, weight="bold"),
        ).pack(pady=5)

        self.preview_text = ctk.CTkTextbox(
            preview_frame,
            wrap="word",
            font=ctk.CTkFont(family="Consolas", size=10),
        )
        self.preview_text.pack(fill="both", expand=True, padx=5, pady=5)

        # Bind text changes for auto-preview
        self.header_text.bind("<KeyRelease>", lambda e: self._auto_preview())
        self.content_text.bind("<KeyRelease>", lambda e: self._auto_preview())
        self.footer_text.bind("<KeyRelease>", lambda e: self._auto_preview())

    def _create_post_processing_ui(self, parent: ctk.CTkFrame) -> None:
        """Create post-processing UI."""
        # Rules list
        rules_frame = ctk.CTkFrame(parent)
        rules_frame.pack(fill="both", expand=True, padx=5, pady=5)

        ctk.CTkLabel(
            rules_frame,
            text="Post-Processing Rules",
            font=ctk.CTkFont(size=12, weight="bold"),
        ).pack(pady=5)

        self.rules_listbox = ctk.CTkTextbox(rules_frame, height=200)
        self.rules_listbox.pack(fill="x", padx=5, pady=5)

        # Add rule button
        add_rule_button = ctk.CTkButton(
            rules_frame,
            text="Add Rule",
            command=self._add_rule,
            width=100,
        )
        add_rule_button.pack(pady=5)

    def _load_template(self) -> None:
        """Load template into editor."""
        self.name_var.set(self.template.name)
        self.header_text.delete("1.0", "end")
        self.header_text.insert("1.0", self.template.header_template)
        self.content_text.delete("1.0", "end")
        self.content_text.insert("1.0", self.template.template_content)
        self.footer_text.delete("1.0", "end")
        self.footer_text.insert("1.0", self.template.footer_template)

        # Update post-processing display
        if self.template.post_processing:
            rules_text = "\n".join([
                f"- {r.name} ({r.rule_type})" for r in self.template.post_processing.rules
            ])
            self.rules_listbox.delete("1.0", "end")
            self.rules_listbox.insert("1.0", rules_text)

    def _save_template(self) -> None:
        """Save template."""
        # Update template from editor
        self.template.name = self.name_var.get()
        self.template.header_template = self.header_text.get("1.0", "end-1c")
        self.template.template_content = self.content_text.get("1.0", "end-1c")
        self.template.footer_template = self.footer_text.get("1.0", "end-1c")

        # Validate
        is_valid, error = self.template.validate()
        if not is_valid:
            from tkinter import messagebox
            messagebox.showerror("Validation Error", f"Template has errors:\n{error}")
            return

        if self.on_save:
            self.on_save(self.template)

    def _validate_template(self) -> None:
        """Validate template syntax."""
        # Update template from editor
        self.template.header_template = self.header_text.get("1.0", "end-1c")
        self.template.template_content = self.content_text.get("1.0", "end-1c")
        self.template.footer_template = self.footer_text.get("1.0", "end-1c")

        is_valid, error = self.template.validate()
        from tkinter import messagebox
        if is_valid:
            messagebox.showinfo("Validation", "Template is valid!")
        else:
            messagebox.showerror("Validation Error", f"Template has errors:\n{error}")

    def _update_preview(self) -> None:
        """Update preview."""
        # Sample content for preview
        sample_content = """# Sample Content

This is a sample markdown content for preview.

## Section 1

Some text here.

## Section 2

More content.
"""

        # Update template from editor
        self.template.header_template = self.header_text.get("1.0", "end-1c")
        self.template.template_content = self.content_text.get("1.0", "end-1c")
        self.template.footer_template = self.footer_text.get("1.0", "end-1c")

        # Render
        try:
            rendered = self.template.render(
                sample_content,
                metadata={"title": "Preview Document", "author": "Preview Author"}
            )
            self.preview_text.delete("1.0", "end")
            self.preview_text.insert("1.0", rendered)

            if self.on_preview:
                self.on_preview(rendered)
        except Exception as e:
            self.preview_text.delete("1.0", "end")
            self.preview_text.insert("1.0", f"Preview Error: {e}")

    def _auto_preview(self) -> None:
        """Auto-update preview on text change."""
        # Debounce: only update after a delay
        self.after(500, self._update_preview)

    def _add_rule(self) -> None:
        """Add post-processing rule."""
        from tkinter import simpledialog

        rule_name = simpledialog.askstring("Add Rule", "Rule name:")
        if not rule_name:
            return

        rule_type = simpledialog.askstring("Rule Type", "Rule type (text_replacement, regex_replacement, etc.):")
        if not rule_type:
            rule_type = "text_replacement"

        pattern = simpledialog.askstring("Pattern", "Pattern (optional):")
        replacement = simpledialog.askstring("Replacement", "Replacement (optional):")

        rule = PostProcessingRule(
            name=rule_name,
            rule_type=rule_type,
            pattern=pattern,
            replacement=replacement,
        )

        if not self.template.post_processing:
            self.template.post_processing = PostProcessingPipeline(name="default")

        self.template.post_processing.add_rule(rule)

        # Update display
        rules_text = "\n".join([
            f"- {r.name} ({r.rule_type})" for r in self.template.post_processing.rules
        ])
        self.rules_listbox.delete("1.0", "end")
        self.rules_listbox.insert("1.0", rules_text)


class TemplateManagerUI(ctk.CTkFrame):
    """UI for managing templates."""

    def __init__(
        self,
        master: Any,
        template_manager: Any,
        on_template_selected: Optional[Callable[[str], None]] = None,
        **kwargs
    ) -> None:
        """
        Initialize template manager UI.
        
        Args:
            master: Parent widget
            template_manager: TemplateManager instance
            on_template_selected: Callback when template is selected
            **kwargs: Additional CTkFrame arguments
        """
        super().__init__(master, **kwargs)
        self.template_manager = template_manager
        self.on_template_selected = on_template_selected

        self._create_widgets()
        self._load_templates()

    def _create_widgets(self) -> None:
        """Create manager widgets."""
        # Header
        header = ctk.CTkFrame(self)
        header.pack(fill="x", padx=10, pady=10)

        ctk.CTkLabel(
            header,
            text="Template Library",
            font=ctk.CTkFont(size=16, weight="bold"),
        ).pack(side="left", padx=10)

        # Category filter
        category_frame = ctk.CTkFrame(self)
        category_frame.pack(fill="x", padx=10, pady=5)

        ctk.CTkLabel(category_frame, text="Category:").pack(side="left", padx=5)
        self.category_var = ctk.StringVar(value="all")
        category_menu = ctk.CTkOptionMenu(
            category_frame,
            values=["all", "technical", "blog", "academic", "minimalist", "custom"],
            variable=self.category_var,
            command=self._filter_templates,
        )
        category_menu.pack(side="left", padx=5)

        # Template list
        list_frame = ctk.CTkFrame(self)
        list_frame.pack(fill="both", expand=True, padx=10, pady=10)

        self.template_listbox = ctk.CTkTextbox(list_frame)
        self.template_listbox.pack(fill="both", expand=True)

        # Buttons
        button_frame = ctk.CTkFrame(self)
        button_frame.pack(fill="x", padx=10, pady=10)

        ctk.CTkButton(
            button_frame,
            text="New Template",
            command=self._new_template,
            width=120,
        ).pack(side="left", padx=5)

        ctk.CTkButton(
            button_frame,
            text="Edit",
            command=self._edit_template,
            width=120,
        ).pack(side="left", padx=5)

        ctk.CTkButton(
            button_frame,
            text="Import",
            command=self._import_template,
            width=120,
        ).pack(side="left", padx=5)

        ctk.CTkButton(
            button_frame,
            text="Export",
            command=self._export_template,
            width=120,
        ).pack(side="left", padx=5)

    def _load_templates(self) -> None:
        """Load templates into list."""
        templates = self.template_manager.get_all_templates()
        self.template_listbox.delete("1.0", "end")

        for i, template in enumerate(templates, 1):
            self.template_listbox.insert(
                "end",
                f"{i}. {template.name} ({template.category.value})\n"
                f"   {template.description}\n\n"
            )

    def _filter_templates(self, category: str) -> None:
        """Filter templates by category."""
        from gui.core.templates import TemplateCategory

        if category == "all":
            templates = self.template_manager.get_all_templates()
        else:
            cat = TemplateCategory(category)
            templates = self.template_manager.get_templates_by_category(cat)

        self.template_listbox.delete("1.0", "end")
        for i, template in enumerate(templates, 1):
            self.template_listbox.insert(
                "end",
                f"{i}. {template.name} ({template.category.value})\n"
                f"   {template.description}\n\n"
            )

    def _new_template(self) -> None:
        """Create new template."""
        # This would open template editor
        pass

    def _edit_template(self) -> None:
        """Edit selected template."""
        # This would open template editor
        pass

    def _import_template(self) -> None:
        """Import template from file."""
        from tkinter import filedialog
        file_path = filedialog.askopenfilename(
            title="Import Template",
            filetypes=[("JSON", "*.json"), ("All Files", "*.*")]
        )
        if file_path:
            template = self.template_manager.import_template(Path(file_path))
            if template:
                self._load_templates()

    def _export_template(self) -> None:
        """Export selected template."""
        from tkinter import filedialog
        # Get selected template (simplified)
        templates = self.template_manager.get_all_templates()
        if templates:
            file_path = filedialog.asksaveasfilename(
                title="Export Template",
                defaultextension=".json",
                filetypes=[("JSON", "*.json"), ("All Files", "*.*")]
            )
            if file_path:
                self.template_manager.export_template(templates[0].template_id, Path(file_path))

