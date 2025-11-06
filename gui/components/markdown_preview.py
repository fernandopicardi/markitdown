"""
Markdown preview component with webview rendering.
"""

import customtkinter as ctk
from tkinter import messagebox
from pathlib import Path
from typing import Optional, Callable, Dict, Any
import logging
import tempfile
import webbrowser
import threading

try:
    import tkinterweb
    HAS_TKINTERWEB = True
except ImportError:
    HAS_TKINTERWEB = False
    try:
        from tkinter import html
        HAS_HTML = True
    except ImportError:
        HAS_HTML = False

from gui.core.markdown_renderer import MarkdownRenderer, RenderOptions, PreviewTheme

logger = logging.getLogger(__name__)


class MarkdownPreviewPanel(ctk.CTkFrame):
    """Markdown preview panel with HTML rendering."""

    def __init__(
        self,
        master: Any,
        renderer: Optional[MarkdownRenderer] = None,
        on_search: Optional[Callable[[str], None]] = None,
        **kwargs
    ) -> None:
        """
        Initialize preview panel.
        
        Args:
            master: Parent widget
            renderer: Markdown renderer instance
            on_search: Callback for search
            **kwargs: Additional CTkFrame arguments
        """
        super().__init__(master, **kwargs)
        self.renderer = renderer or MarkdownRenderer()
        self.on_search = on_search
        self.current_html: Optional[str] = None
        self.temp_file: Optional[Path] = None

        self._create_widgets()

    def _create_widgets(self) -> None:
        """Create preview widgets."""
        # Toolbar
        toolbar = ctk.CTkFrame(self)
        toolbar.pack(fill="x", padx=5, pady=5)

        # Search
        search_frame = ctk.CTkFrame(toolbar)
        search_frame.pack(side="left", padx=5)

        ctk.CTkLabel(search_frame, text="Search:").pack(side="left", padx=5)
        self.search_var = ctk.StringVar()
        search_entry = ctk.CTkEntry(
            search_frame,
            textvariable=self.search_var,
            width=200,
            placeholder_text="Search in preview..."
        )
        search_entry.pack(side="left", padx=5)
        search_entry.bind("<Return>", lambda e: self._do_search())

        ctk.CTkButton(
            search_frame,
            text="Search",
            command=self._do_search,
            width=80,
        ).pack(side="left", padx=5)

        # Zoom controls
        zoom_frame = ctk.CTkFrame(toolbar)
        zoom_frame.pack(side="right", padx=5)

        ctk.CTkButton(
            zoom_frame,
            text="-",
            command=self._zoom_out,
            width=40,
        ).pack(side="left", padx=2)

        self.zoom_label = ctk.CTkLabel(zoom_frame, text="100%")
        self.zoom_label.pack(side="left", padx=5)

        ctk.CTkButton(
            zoom_frame,
            text="+",
            command=self._zoom_in,
            width=40,
        ).pack(side="left", padx=2)

        # Preview area
        preview_frame = ctk.CTkFrame(self)
        preview_frame.pack(fill="both", expand=True, padx=5, pady=5)

        if HAS_TKINTERWEB:
            # Use tkinterweb for HTML rendering
            try:
                self.html_frame = tkinterweb.HtmlFrame(
                    preview_frame,
                    messages_enabled=False
                )
                self.html_frame.pack(fill="both", expand=True)
            except Exception as e:
                logger.warning(f"Failed to create tkinterweb frame: {e}")
                self._create_fallback_preview(preview_frame)
        else:
            # Fallback: use text widget or open in browser
            self._create_fallback_preview(preview_frame)

    def _create_fallback_preview(self, parent: ctk.CTkFrame) -> None:
        """Create fallback preview (text widget or browser)."""
        # Use text widget to show HTML source or message
        self.preview_text = ctk.CTkTextbox(parent)
        self.preview_text.pack(fill="both", expand=True)
        self.preview_text.insert("1.0", "Preview: HTML rendering not available.\n")
        self.preview_text.insert("end", "Rendered HTML will be shown here or opened in browser.")

    def update_preview(self, markdown_text: str) -> None:
        """
        Update preview with new markdown.
        
        Args:
            markdown_text: Markdown text to preview
        """
        try:
            # Render to HTML
            html = self.renderer.render(markdown_text)
            self.current_html = html

            # Update preview
            if hasattr(self, 'html_frame'):
                # Use tkinterweb
                self.html_frame.load_html(html)
            elif hasattr(self, 'preview_text'):
                # Show HTML source or message
                self.preview_text.delete("1.0", "end")
                self.preview_text.insert("1.0", f"Preview (HTML source):\n\n{html[:1000]}...")
            else:
                # Open in browser
                self._open_in_browser(html)

        except Exception as e:
            logger.error(f"Error updating preview: {e}")
            if hasattr(self, 'preview_text'):
                self.preview_text.delete("1.0", "end")
                self.preview_text.insert("1.0", f"Preview Error: {e}")

    def _open_in_browser(self, html: str) -> None:
        """Open preview in browser."""
        try:
            # Create temp file
            with tempfile.NamedTemporaryFile(mode='w', suffix='.html', delete=False, encoding='utf-8') as f:
                f.write(html)
                self.temp_file = Path(f.name)

            # Open in browser
            webbrowser.open(f"file://{self.temp_file}")
        except Exception as e:
            logger.error(f"Failed to open in browser: {e}")

    def _do_search(self) -> None:
        """Perform search in preview."""
        query = self.search_var.get()
        if query and self.on_search:
            self.on_search(query)

    def _zoom_in(self) -> None:
        """Zoom in."""
        current_zoom = self.renderer.options.zoom_level
        new_zoom = min(current_zoom + 0.1, 2.0)
        self.renderer.options.zoom_level = new_zoom
        self.zoom_label.configure(text=f"{int(new_zoom * 100)}%")
        if self.current_html:
            self.update_preview("")  # Re-render with new zoom

    def _zoom_out(self) -> None:
        """Zoom out."""
        current_zoom = self.renderer.options.zoom_level
        new_zoom = max(current_zoom - 0.1, 0.5)
        self.renderer.options.zoom_level = new_zoom
        self.zoom_label.configure(text=f"{int(new_zoom * 100)}%")
        if self.current_html:
            self.update_preview("")  # Re-render with new zoom

    def copy_html(self) -> str:
        """
        Copy rendered HTML to clipboard.
        
        Returns:
            HTML string
        """
        if self.current_html:
            self.clipboard_clear()
            self.clipboard_append(self.current_html)
            return self.current_html
        return ""

    def set_theme(self, theme: PreviewTheme) -> None:
        """
        Set preview theme.
        
        Args:
            theme: Theme to set
        """
        self.renderer.options.theme = theme
        if self.current_html:
            self.update_preview("")  # Re-render with new theme

    def set_dark_mode(self, dark: bool) -> None:
        """
        Set dark mode.
        
        Args:
            dark: True for dark mode
        """
        self.renderer.options.dark_mode = dark
        if self.current_html:
            self.update_preview("")  # Re-render with dark mode


class SplitPreviewView(ctk.CTkFrame):
    """Split view: Markdown source | Preview."""

    def __init__(
        self,
        master: Any,
        renderer: Optional[MarkdownRenderer] = None,
        on_content_change: Optional[Callable[[str], None]] = None,
        **kwargs
    ) -> None:
        """
        Initialize split view.
        
        Args:
            master: Parent widget
            renderer: Markdown renderer
            on_content_change: Callback when content changes
            **kwargs: Additional CTkFrame arguments
        """
        super().__init__(master, **kwargs)
        self.renderer = renderer or MarkdownRenderer()
        self.on_content_change = on_content_change
        self.sync_scroll = True

        self._create_widgets()

    def _create_widgets(self) -> None:
        """Create split view widgets."""
        # Split panes
        self.paned_window = ctk.CTkFrame(self)
        self.paned_window.pack(fill="both", expand=True)

        # Left: Markdown editor
        left_frame = ctk.CTkFrame(self.paned_window)
        left_frame.pack(side="left", fill="both", expand=True, padx=5)

        ctk.CTkLabel(
            left_frame,
            text="Markdown Source",
            font=ctk.CTkFont(size=12, weight="bold"),
        ).pack(pady=5)

        self.markdown_text = ctk.CTkTextbox(
            left_frame,
            wrap="none",
            font=ctk.CTkFont(family="Consolas", size=11),
        )
        self.markdown_text.pack(fill="both", expand=True, padx=5, pady=5)
        self.markdown_text.bind("<KeyRelease>", self._on_markdown_change)
        self.markdown_text.bind("<Button-1>", self._on_markdown_scroll)

        # Right: Preview
        right_frame = ctk.CTkFrame(self.paned_window)
        right_frame.pack(side="right", fill="both", expand=True, padx=5)

        ctk.CTkLabel(
            right_frame,
            text="Preview",
            font=ctk.CTkFont(size=12, weight="bold"),
        ).pack(pady=5)

        self.preview_panel = MarkdownPreviewPanel(
            right_frame,
            renderer=self.renderer,
        )
        self.preview_panel.pack(fill="both", expand=True)

        # Sync scroll checkbox
        sync_frame = ctk.CTkFrame(self)
        sync_frame.pack(fill="x", padx=10, pady=5)

        self.sync_var = ctk.BooleanVar(value=True)
        sync_checkbox = ctk.CTkCheckBox(
            sync_frame,
            text="Sync Scroll",
            variable=self.sync_var,
            command=self._toggle_sync,
        )
        sync_checkbox.pack(side="left", padx=5)

    def _on_markdown_change(self, event: Any = None) -> None:
        """Handle markdown text change."""
        content = self.markdown_text.get("1.0", "end-1c")
        self.preview_panel.update_preview(content)
        
        if self.on_content_change:
            self.on_content_change(content)

    def _on_markdown_scroll(self, event: Any = None) -> None:
        """Handle markdown scroll (for sync)."""
        if self.sync_scroll and self.sync_var.get():
            # Sync preview scroll with markdown scroll
            # This is a simplified version
            pass

    def _toggle_sync(self) -> None:
        """Toggle scroll synchronization."""
        self.sync_scroll = self.sync_var.get()

    def set_content(self, markdown_text: str) -> None:
        """
        Set markdown content.
        
        Args:
            markdown_text: Markdown text
        """
        self.markdown_text.delete("1.0", "end")
        self.markdown_text.insert("1.0", markdown_text)
        self._on_markdown_change()

    def get_content(self) -> str:
        """
        Get current markdown content.
        
        Returns:
            Markdown text
        """
        return self.markdown_text.get("1.0", "end-1c")

