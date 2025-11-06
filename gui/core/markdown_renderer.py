"""
Markdown renderer with HTML output and extensions support.

This module provides sophisticated Markdown rendering with syntax highlighting,
extensions support, and theme management.
"""

import re
import logging
from pathlib import Path
from typing import Optional, Dict, Any, List
from enum import Enum
from dataclasses import dataclass, field

try:
    from markdown_it import MarkdownIt
    from markdown_it.tree import SyntaxTreeNode
    from mdit_py_plugins.front_matter import front_matter_plugin
    from mdit_py_plugins.footnote import footnote_plugin
    from mdit_py_plugins.tasklists import tasklists_plugin
    from mdit_py_plugins.emoji import emoji_plugin
    from mdit_py_plugins.myst_blocks import myst_block_plugin
except ImportError:
    MarkdownIt = None

try:
    from pygments import highlight
    from pygments.lexers import get_lexer_by_name, guess_lexer_for_filename
    from pygments.formatters import HtmlFormatter
    from pygments.util import ClassNotFound
except ImportError:
    highlight = None
    HtmlFormatter = None

logger = logging.getLogger(__name__)


class PreviewTheme(Enum):
    """Preview themes."""

    GITHUB = "github"
    READTHEDOCS = "readthedocs"
    GITHUB_DARK = "github_dark"
    MINIMAL = "minimal"
    CUSTOM = "custom"


@dataclass
class RenderOptions:
    """Options for Markdown rendering."""

    enable_tables: bool = True
    enable_footnotes: bool = True
    enable_tasklists: bool = True
    enable_emoji: bool = True
    enable_math: bool = True
    enable_mermaid: bool = True
    syntax_highlighting: bool = True
    theme: PreviewTheme = PreviewTheme.GITHUB
    dark_mode: bool = False
    zoom_level: float = 1.0
    line_numbers: bool = False
    wrap_code: bool = True


class MarkdownRenderer:
    """Sophisticated Markdown renderer with extensions."""

    def __init__(self, options: Optional[RenderOptions] = None) -> None:
        """
        Initialize Markdown renderer.
        
        Args:
            options: Rendering options
        """
        self.options = options or RenderOptions()
        self.md: Optional[MarkdownIt] = None
        self._init_markdown_parser()

    def _init_markdown_parser(self) -> None:
        """Initialize Markdown parser with extensions."""
        if MarkdownIt is None:
            logger.warning("markdown-it-py not available, using fallback")
            return

        # Create parser with options
        self.md = MarkdownIt("gfm-like", {
            "html": True,
            "linkify": True,
            "typographer": True,
            "breaks": True,
        })

        # Add extensions
        if self.options.enable_footnotes:
            try:
                self.md.use(footnote_plugin)
            except Exception as e:
                logger.warning(f"Failed to load footnote plugin: {e}")

        if self.options.enable_tasklists:
            try:
                self.md.use(tasklists_plugin)
            except Exception as e:
                logger.warning(f"Failed to load tasklists plugin: {e}")

        if self.options.enable_emoji:
            try:
                self.md.use(emoji_plugin)
            except Exception as e:
                logger.warning(f"Failed to load emoji plugin: {e}")

        # Front matter
        try:
            self.md.use(front_matter_plugin)
        except Exception as e:
            logger.warning(f"Failed to load front_matter plugin: {e}")

    def render(self, markdown_text: str) -> str:
        """
        Render Markdown to HTML.
        
        Args:
            markdown_text: Markdown text to render
            
        Returns:
            HTML string
        """
        if self.md is None:
            # Fallback to simple rendering
            return self._fallback_render(markdown_text)

        try:
            # Parse Markdown
            tokens = self.md.parse(markdown_text)
            
            # Render to HTML
            html = self.md.render(markdown_text)
            
            # Post-process: syntax highlighting, math, mermaid
            html = self._post_process(html, markdown_text)
            
            # Wrap in full HTML document
            return self._wrap_html(html)
            
        except Exception as e:
            logger.error(f"Error rendering Markdown: {e}")
            return self._fallback_render(markdown_text)

    def _post_process(self, html: str, markdown_text: str) -> str:
        """
        Post-process HTML: syntax highlighting, math, mermaid.
        
        Args:
            html: HTML to process
            markdown_text: Original markdown for context
            
        Returns:
            Processed HTML
        """
        # Syntax highlighting for code blocks
        if self.options.syntax_highlighting and highlight:
            html = self._highlight_code_blocks(html)
        
        # Math rendering (KaTeX)
        if self.options.enable_math:
            html = self._render_math(html)
        
        # Mermaid diagrams
        if self.options.enable_mermaid:
            html = self._render_mermaid(html)
        
        return html

    def _highlight_code_blocks(self, html: str) -> str:
        """
        Add syntax highlighting to code blocks.
        
        Args:
            html: HTML with code blocks
            
        Returns:
            HTML with highlighted code
        """
        if not highlight or not HtmlFormatter:
            return html

        # Find code blocks
        pattern = r'<pre><code(?:\s+class="language-(\w+)")?>(.*?)</code></pre>'
        
        def replace_code(match):
            lang = match.group(1) or ""
            code = match.group(2)
            # Unescape HTML entities
            code = code.replace('&lt;', '<').replace('&gt;', '>').replace('&amp;', '&')
            
            try:
                if lang:
                    lexer = get_lexer_by_name(lang, stripall=True)
                else:
                    lexer = guess_lexer_for_filename("", code)
            except ClassNotFound:
                lexer = get_lexer_by_name("text", stripall=True)
            
            formatter = HtmlFormatter(
                style="github-dark" if self.options.dark_mode else "github",
                linenos=self.options.line_numbers,
                wrapcode=self.options.wrap_code,
                cssclass="highlight"
            )
            
            highlighted = highlight(code, lexer, formatter)
            return highlighted
        
        return re.sub(pattern, replace_code, html, flags=re.DOTALL)

    def _render_math(self, html: str) -> str:
        """
        Render math expressions with KaTeX.
        
        Args:
            html: HTML with math expressions
            
        Returns:
            HTML with rendered math (KaTeX will render on page load)
        """
        # Mark inline math: $...$ (KaTeX will render)
        html = re.sub(
            r'\$([^$\n]+)\$',
            r'<span class="math-inline">\1</span>',
            html
        )
        
        # Mark block math: $$...$$ (KaTeX will render)
        html = re.sub(
            r'\$\$([^$]+)\$\$',
            r'<div class="math-block">\1</div>',
            html,
            flags=re.DOTALL
        )
        
        return html

    def _render_mermaid(self, html: str) -> str:
        """
        Render Mermaid diagrams.
        
        Args:
            html: HTML with mermaid code blocks
            
        Returns:
            HTML with rendered diagrams
        """
        # Find mermaid code blocks
        pattern = r'<pre><code(?:\s+class="language-mermaid")?>(.*?)</code></pre>'
        
        def replace_mermaid(match):
            diagram = match.group(1)
            diagram = diagram.replace('&lt;', '<').replace('&gt;', '>').replace('&amp;', '&')
            return f'<div class="mermaid">{diagram}</div>'
        
        return re.sub(pattern, replace_mermaid, html, flags=re.DOTALL)

    def _wrap_html(self, html: str) -> str:
        """
        Wrap HTML in full document with theme and styles.
        
        Args:
            html: Body HTML
            
        Returns:
            Complete HTML document
        """
        theme_css = self._get_theme_css()
        katex_css = self._get_katex_css()
        mermaid_js = self._get_mermaid_js()
        pygments_css = self._get_pygments_css()
        
        zoom_style = f"zoom: {self.options.zoom_level};" if self.options.zoom_level != 1.0 else ""
        
        return f"""<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Markdown Preview</title>
    <style>
        {theme_css}
        {pygments_css}
        {katex_css}
        body {{
            {zoom_style}
        }}
    </style>
    {mermaid_js}
</head>
<body class="{'dark' if self.options.dark_mode else 'light'}">
    <div class="markdown-body">
        {html}
    </div>
    <script>
        // Mermaid initialization
        if (typeof mermaid !== 'undefined') {{
            mermaid.initialize({{ startOnLoad: true, theme: '{'dark' if self.options.dark_mode else 'default'}' }});
        }}
        
        // KaTeX rendering
        if (typeof renderMathInElement !== 'undefined') {{
            renderMathInElement(document.body);
        }}
    </script>
</body>
</html>"""

    def _get_theme_css(self) -> str:
        """Get CSS for selected theme."""
        themes = {
            PreviewTheme.GITHUB: self._github_theme_css(),
            PreviewTheme.READTHEDOCS: self._readthedocs_theme_css(),
            PreviewTheme.GITHUB_DARK: self._github_dark_theme_css(),
            PreviewTheme.MINIMAL: self._minimal_theme_css(),
        }
        return themes.get(self.options.theme, themes[PreviewTheme.GITHUB])

    def _github_theme_css(self) -> str:
        """GitHub theme CSS."""
        return """
        body {
            font-family: -apple-system, BlinkMacSystemFont, "Segoe UI", Helvetica, Arial, sans-serif;
            line-height: 1.6;
            color: #24292e;
            background-color: #ffffff;
            max-width: 980px;
            margin: 0 auto;
            padding: 20px;
        }
        .markdown-body {
            font-size: 16px;
        }
        .markdown-body h1, .markdown-body h2 {
            border-bottom: 1px solid #eaecef;
            padding-bottom: 0.3em;
        }
        .markdown-body code {
            background-color: rgba(27, 31, 35, 0.05);
            border-radius: 3px;
            padding: 0.2em 0.4em;
            font-size: 85%;
        }
        .markdown-body pre {
            background-color: #f6f8fa;
            border-radius: 3px;
            padding: 16px;
            overflow: auto;
        }
        .markdown-body table {
            border-collapse: collapse;
            border-spacing: 0;
        }
        .markdown-body table th, .markdown-body table td {
            border: 1px solid #dfe2e5;
            padding: 6px 13px;
        }
        .markdown-body table th {
            background-color: #f6f8fa;
            font-weight: 600;
        }
        """

    def _readthedocs_theme_css(self) -> str:
        """ReadTheDocs theme CSS."""
        return """
        body {
            font-family: "Lato", "proxima-nova", "Helvetica Neue", Arial, sans-serif;
            line-height: 1.6;
            color: #3e4349;
            background-color: #ffffff;
            max-width: 800px;
            margin: 0 auto;
            padding: 20px;
        }
        .markdown-body {
            font-size: 16px;
        }
        .markdown-body h1 {
            color: #2980b9;
            border-bottom: 2px solid #2980b9;
        }
        .markdown-body h2 {
            color: #3498db;
        }
        .markdown-body code {
            background-color: #f4f4f4;
            padding: 2px 4px;
            border-radius: 3px;
        }
        .markdown-body pre {
            background-color: #f4f4f4;
            border-left: 4px solid #2980b9;
            padding: 16px;
        }
        """

    def _github_dark_theme_css(self) -> str:
        """GitHub Dark theme CSS."""
        return """
        body {
            font-family: -apple-system, BlinkMacSystemFont, "Segoe UI", Helvetica, Arial, sans-serif;
            line-height: 1.6;
            color: #c9d1d9;
            background-color: #0d1117;
            max-width: 980px;
            margin: 0 auto;
            padding: 20px;
        }
        .markdown-body {
            font-size: 16px;
        }
        .markdown-body h1, .markdown-body h2 {
            border-bottom: 1px solid #30363d;
            padding-bottom: 0.3em;
        }
        .markdown-body code {
            background-color: rgba(110, 118, 129, 0.4);
            border-radius: 3px;
            padding: 0.2em 0.4em;
            font-size: 85%;
            color: #c9d1d9;
        }
        .markdown-body pre {
            background-color: #161b22;
            border-radius: 3px;
            padding: 16px;
            overflow: auto;
        }
        .markdown-body table th, .markdown-body table td {
            border: 1px solid #30363d;
        }
        .markdown-body table th {
            background-color: #161b22;
        }
        """

    def _minimal_theme_css(self) -> str:
        """Minimal theme CSS."""
        return """
        body {
            font-family: Georgia, serif;
            line-height: 1.8;
            color: #333;
            background-color: #ffffff;
            max-width: 700px;
            margin: 0 auto;
            padding: 40px 20px;
        }
        .markdown-body {
            font-size: 18px;
        }
        .markdown-body h1, .markdown-body h2 {
            margin-top: 1.5em;
        }
        .markdown-body code {
            background-color: #f5f5f5;
            padding: 2px 4px;
        }
        .markdown-body pre {
            background-color: #f5f5f5;
            padding: 16px;
            border-radius: 4px;
        }
        """

    def _get_pygments_css(self) -> str:
        """Get Pygments CSS for syntax highlighting."""
        if not HtmlFormatter:
            return ""
        
        formatter = HtmlFormatter(
            style="github-dark" if self.options.dark_mode else "github"
        )
        return f"<style>{formatter.get_style_defs('.highlight')}</style>"

    def _get_katex_css(self) -> str:
        """Get KaTeX CSS for math rendering."""
        return """
        <link rel="stylesheet" href="https://cdn.jsdelivr.net/npm/katex@0.16.9/dist/katex.min.css">
        <script defer src="https://cdn.jsdelivr.net/npm/katex@0.16.9/dist/katex.min.js"></script>
        <script defer src="https://cdn.jsdelivr.net/npm/katex@0.16.9/dist/contrib/auto-render.min.js"></script>
        <style>
            .math-inline, .math-block {
                margin: 0.5em 0;
            }
        </style>
        """

    def _get_mermaid_js(self) -> str:
        """Get Mermaid JS for diagram rendering."""
        return """
        <script src="https://cdn.jsdelivr.net/npm/mermaid@10/dist/mermaid.min.js"></script>
        <style>
            .mermaid {
                text-align: center;
                margin: 1em 0;
            }
        </style>
        """

    def _fallback_render(self, markdown_text: str) -> str:
        """Fallback simple rendering if markdown-it not available."""
        # Very basic markdown rendering
        html = markdown_text
        html = re.sub(r'^# (.+)$', r'<h1>\1</h1>', html, flags=re.MULTILINE)
        html = re.sub(r'^## (.+)$', r'<h2>\1</h2>', html, flags=re.MULTILINE)
        html = re.sub(r'^### (.+)$', r'<h3>\1</h3>', html, flags=re.MULTILINE)
        html = re.sub(r'\*\*(.+?)\*\*', r'<strong>\1</strong>', html)
        html = re.sub(r'\*(.+?)\*', r'<em>\1</em>', html)
        html = re.sub(r'`(.+?)`', r'<code>\1</code>', html)
        html = html.replace('\n', '<br>\n')
        return self._wrap_html(html)

    def get_html(self, markdown_text: str) -> str:
        """
        Get rendered HTML.
        
        Args:
            markdown_text: Markdown text
            
        Returns:
            HTML string
        """
        return self.render(markdown_text)

    def export_html(self, markdown_text: str, output_path: Path) -> bool:
        """
        Export rendered HTML to file.
        
        Args:
            markdown_text: Markdown text
            output_path: Output file path
            
        Returns:
            True if successful
        """
        try:
            html = self.render(markdown_text)
            with open(output_path, "w", encoding="utf-8") as f:
                f.write(html)
            return True
        except Exception as e:
            logger.error(f"Failed to export HTML: {e}")
            return False

    def export_pdf(self, markdown_text: str, output_path: Path) -> bool:
        """
        Export rendered HTML as PDF.
        
        Args:
            markdown_text: Markdown text
            output_path: Output PDF path
            
        Returns:
            True if successful
        """
        try:
            # Render to HTML first
            html = self.render(markdown_text)
            
            # Use weasyprint for PDF generation
            try:
                from weasyprint import HTML, CSS
                HTML(string=html).write_pdf(output_path)
                return True
            except ImportError:
                logger.error("weasyprint not available for PDF export")
                return False
        except Exception as e:
            logger.error(f"Failed to export PDF: {e}")
            return False

