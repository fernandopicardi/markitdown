"""
Sophisticated Markdown preview window with all features.

Features:
- Split view (Markdown | Preview)
- Scroll synchronization
- Presentation mode
- Export HTML/PDF
- Themes
- Zoom
- Dark/Light mode
- Search
- Copy HTML
"""

import customtkinter as ctk
from tkinter import filedialog, messagebox
from pathlib import Path
from typing import Optional, Dict, Any
import logging

from gui.core.markdown_renderer import MarkdownRenderer, RenderOptions, PreviewTheme
from gui.components.markdown_preview import MarkdownPreviewPanel, SplitPreviewView

logger = logging.getLogger(__name__)


class MarkdownPreviewWindow(ctk.CTk):
    """Sophisticated Markdown preview window."""

    def __init__(
        self,
        markdown_text: str = "",
        **kwargs
    ) -> None:
        """
        Initialize preview window.
        
        Args:
            markdown_text: Initial markdown text
            **kwargs: Additional CTk arguments
        """
        super().__init__(**kwargs)
        self.markdown_text = markdown_text
        
        # Create renderer
        self.renderer = MarkdownRenderer()
        
        # Presentation mode
        self.presentation_mode = False
        self.presentation_window: Optional[ctk.CTkToplevel] = None

        self._setup_window()
        self._create_layout()
        self._load_content(markdown_text)

        logger.info("Markdown preview window initialized")

    def _setup_window(self) -> None:
        """Configure window properties."""
        self.title("MarkItDown - Markdown Preview")
        self.geometry("1400x900")
        self.minsize(1200, 700)

    def _create_layout(self) -> None:
        """Create main layout."""
        # Top toolbar
        toolbar = ctk.CTkFrame(self)
        toolbar.pack(fill="x", padx=10, pady=10)

        # Left side - File operations
        left_toolbar = ctk.CTkFrame(toolbar)
        left_toolbar.pack(side="left", padx=5)

        ctk.CTkButton(
            left_toolbar,
            text="Open",
            command=self._open_file,
            width=80,
        ).pack(side="left", padx=2)

        ctk.CTkButton(
            left_toolbar,
            text="Save",
            command=self._save_file,
            width=80,
        ).pack(side="left", padx=2)

        # Center - View controls
        center_toolbar = ctk.CTkFrame(toolbar)
        center_toolbar.pack(side="left", padx=20)

        # View mode
        ctk.CTkLabel(center_toolbar, text="View:").pack(side="left", padx=5)
        self.view_mode_var = ctk.StringVar(value="split")
        view_menu = ctk.CTkOptionMenu(
            center_toolbar,
            values=["split", "markdown", "preview"],
            variable=self.view_mode_var,
            command=self._change_view_mode,
            width=120,
        )
        view_menu.pack(side="left", padx=5)

        # Theme
        ctk.CTkLabel(center_toolbar, text="Theme:").pack(side="left", padx=5)
        self.theme_var = ctk.StringVar(value="github")
        theme_menu = ctk.CTkOptionMenu(
            center_toolbar,
            values=["github", "readthedocs", "github_dark", "minimal"],
            variable=self.theme_var,
            command=self._change_theme,
            width=120,
        )
        theme_menu.pack(side="left", padx=5)

        # Dark mode toggle
        self.dark_mode_var = ctk.BooleanVar(value=False)
        dark_checkbox = ctk.CTkCheckBox(
            center_toolbar,
            text="Dark",
            variable=self.dark_mode_var,
            command=self._toggle_dark_mode,
        )
        dark_checkbox.pack(side="left", padx=5)

        # Right side - Export and presentation
        right_toolbar = ctk.CTkFrame(toolbar)
        right_toolbar.pack(side="right", padx=5)

        ctk.CTkButton(
            right_toolbar,
            text="Export HTML",
            command=self._export_html,
            width=100,
        ).pack(side="left", padx=2)

        ctk.CTkButton(
            right_toolbar,
            text="Export PDF",
            command=self._export_pdf,
            width=100,
        ).pack(side="left", padx=2)

        ctk.CTkButton(
            right_toolbar,
            text="Copy HTML",
            command=self._copy_html,
            width=100,
        ).pack(side="left", padx=2)

        ctk.CTkButton(
            right_toolbar,
            text="Presentation",
            command=self._toggle_presentation,
            width=100,
        ).pack(side="left", padx=2)

        # Main content area
        self.content_frame = ctk.CTkFrame(self)
        self.content_frame.pack(fill="both", expand=True, padx=10, pady=10)

        # Create split view
        self.split_view = SplitPreviewView(
            self.content_frame,
            renderer=self.renderer,
            on_content_change=self._on_content_change,
        )
        self.split_view.pack(fill="both", expand=True)

        # Store references for view switching
        self.current_view = "split"

    def _load_content(self, markdown_text: str) -> None:
        """Load markdown content."""
        if hasattr(self, 'split_view'):
            self.split_view.set_content(markdown_text)

    def _change_view_mode(self, mode: str) -> None:
        """Change view mode."""
        # Clear current view
        for widget in self.content_frame.winfo_children():
            widget.destroy()

        if mode == "split":
            self.split_view = SplitPreviewView(
                self.content_frame,
                renderer=self.renderer,
                on_content_change=self._on_content_change,
            )
            self.split_view.pack(fill="both", expand=True)
            self.split_view.set_content(self.markdown_text)
            self.current_view = "split"

        elif mode == "markdown":
            # Markdown only
            markdown_frame = ctk.CTkFrame(self.content_frame)
            markdown_frame.pack(fill="both", expand=True)

            self.markdown_text_widget = ctk.CTkTextbox(
                markdown_frame,
                wrap="none",
                font=ctk.CTkFont(family="Consolas", size=11),
            )
            self.markdown_text_widget.pack(fill="both", expand=True, padx=5, pady=5)
            self.markdown_text_widget.insert("1.0", self.markdown_text)
            self.current_view = "markdown"

        elif mode == "preview":
            # Preview only
            preview_frame = ctk.CTkFrame(self.content_frame)
            preview_frame.pack(fill="both", expand=True)

            self.preview_only = MarkdownPreviewPanel(
                preview_frame,
                renderer=self.renderer,
            )
            self.preview_only.pack(fill="both", expand=True)
            self.preview_only.update_preview(self.markdown_text)
            self.current_view = "preview"

    def _change_theme(self, theme_name: str) -> None:
        """Change preview theme."""
        theme_map = {
            "github": PreviewTheme.GITHUB,
            "readthedocs": PreviewTheme.READTHEDOCS,
            "github_dark": PreviewTheme.GITHUB_DARK,
            "minimal": PreviewTheme.MINIMAL,
        }
        theme = theme_map.get(theme_name, PreviewTheme.GITHUB)
        self.renderer.options.theme = theme
        self._update_preview()

    def _toggle_dark_mode(self) -> None:
        """Toggle dark mode."""
        dark = self.dark_mode_var.get()
        self.renderer.options.dark_mode = dark
        self._update_preview()

    def _update_preview(self) -> None:
        """Update preview with current content."""
        if hasattr(self, 'split_view'):
            self.split_view._on_markdown_change()
        elif hasattr(self, 'preview_only'):
            self.preview_only.update_preview(self.markdown_text)

    def _on_content_change(self, content: str) -> None:
        """Handle content change."""
        self.markdown_text = content

    def _open_file(self) -> None:
        """Open markdown file."""
        file_path = filedialog.askopenfilename(
            title="Open Markdown File",
            filetypes=[("Markdown", "*.md"), ("Text", "*.txt"), ("All Files", "*.*")]
        )
        if file_path:
            try:
                with open(file_path, "r", encoding="utf-8") as f:
                    content = f.read()
                self.markdown_text = content
                self._load_content(content)
                messagebox.showinfo("Success", "File loaded successfully!")
            except Exception as e:
                messagebox.showerror("Error", f"Failed to load file: {e}")

    def _save_file(self) -> None:
        """Save markdown file."""
        file_path = filedialog.asksaveasfilename(
            title="Save Markdown File",
            defaultextension=".md",
            filetypes=[("Markdown", "*.md"), ("Text", "*.txt"), ("All Files", "*.*")]
        )
        if file_path:
            try:
                content = self.split_view.get_content() if hasattr(self, 'split_view') else self.markdown_text
                with open(file_path, "w", encoding="utf-8") as f:
                    f.write(content)
                messagebox.showinfo("Success", "File saved successfully!")
            except Exception as e:
                messagebox.showerror("Error", f"Failed to save file: {e}")

    def _export_html(self) -> None:
        """Export preview as HTML."""
        file_path = filedialog.asksaveasfilename(
            title="Export HTML",
            defaultextension=".html",
            filetypes=[("HTML", "*.html"), ("All Files", "*.*")]
        )
        if file_path:
            content = self.split_view.get_content() if hasattr(self, 'split_view') else self.markdown_text
            if self.renderer.export_html(content, Path(file_path)):
                messagebox.showinfo("Success", "HTML exported successfully!")
            else:
                messagebox.showerror("Error", "Failed to export HTML")

    def _export_pdf(self) -> None:
        """Export preview as PDF."""
        file_path = filedialog.asksaveasfilename(
            title="Export PDF",
            defaultextension=".pdf",
            filetypes=[("PDF", "*.pdf"), ("All Files", "*.*")]
        )
        if file_path:
            content = self.split_view.get_content() if hasattr(self, 'split_view') else self.markdown_text
            if self.renderer.export_pdf(content, Path(file_path)):
                messagebox.showinfo("Success", "PDF exported successfully!")
            else:
                messagebox.showerror("Error", "Failed to export PDF. Make sure weasyprint is installed.")

    def _copy_html(self) -> None:
        """Copy rendered HTML to clipboard."""
        content = self.split_view.get_content() if hasattr(self, 'split_view') else self.markdown_text
        html = self.renderer.render(content)
        self.clipboard_clear()
        self.clipboard_append(html)
        messagebox.showinfo("Success", "HTML copied to clipboard!")

    def _toggle_presentation(self) -> None:
        """Toggle presentation mode (fullscreen)."""
        if not self.presentation_mode:
            self._start_presentation()
        else:
            self._stop_presentation()

    def _start_presentation(self) -> None:
        """Start presentation mode."""
        self.presentation_mode = True
        
        # Create fullscreen window
        self.presentation_window = ctk.CTkToplevel(self)
        self.presentation_window.title("Markdown Preview - Presentation Mode")
        self.presentation_window.attributes("-fullscreen", True)
        
        # Create preview in presentation window
        preview_frame = ctk.CTkFrame(self.presentation_window)
        preview_frame.pack(fill="both", expand=True, padx=20, pady=20)

        presentation_preview = MarkdownPreviewPanel(
            preview_frame,
            renderer=self.renderer,
        )
        presentation_preview.pack(fill="both", expand=True)
        
        content = self.split_view.get_content() if hasattr(self, 'split_view') else self.markdown_text
        presentation_preview.update_preview(content)

        # Close button
        close_button = ctk.CTkButton(
            self.presentation_window,
            text="Exit Presentation (ESC)",
            command=self._stop_presentation,
            width=200,
        )
        close_button.pack(pady=10)

        # Bind ESC key
        self.presentation_window.bind("<Escape>", lambda e: self._stop_presentation())

    def _stop_presentation(self) -> None:
        """Stop presentation mode."""
        if self.presentation_window:
            self.presentation_window.destroy()
            self.presentation_window = None
        self.presentation_mode = False

    def run(self) -> None:
        """Start the window."""
        logger.info("Starting markdown preview window")
        self.mainloop()


def show_preview(markdown_text: str = "") -> None:
    """
    Show markdown preview window.
    
    Args:
        markdown_text: Markdown text to preview
    """
    window = MarkdownPreviewWindow(markdown_text=markdown_text)
    window.run()

