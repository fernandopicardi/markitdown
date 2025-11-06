"""
Document comparison system for MarkItDown GUI.

This module provides comparison between original documents and
converted Markdown with visual diff, statistics, and navigation.
"""

import difflib
import logging
from pathlib import Path
from typing import List, Dict, Optional, Tuple, Any
from dataclasses import dataclass, field
from enum import Enum
import re

try:
    import fitz  # PyMuPDF
    HAS_PYMUPDF = True
except ImportError:
    HAS_PYMUPDF = False

try:
    from docx import Document
    HAS_DOCX = True
except ImportError:
    HAS_DOCX = False

logger = logging.getLogger(__name__)


class DiffType(Enum):
    """Types of differences."""

    ADDED = "added"
    REMOVED = "removed"
    MODIFIED = "modified"
    UNCHANGED = "unchanged"


@dataclass
class DiffSegment:
    """A segment of difference."""

    diff_type: DiffType
    original_text: str
    converted_text: str
    line_number: int
    start_pos: int = 0
    end_pos: int = 0


@dataclass
class ConversionStatistics:
    """Statistics about conversion."""

    total_chars_original: int = 0
    total_chars_converted: int = 0
    chars_preserved: int = 0
    chars_added: int = 0
    chars_removed: int = 0
    chars_modified: int = 0
    preservation_percentage: float = 0.0
    elements_lost: List[str] = field(default_factory=list)
    formatting_changed: List[str] = field(default_factory=list)
    total_differences: int = 0
    added_segments: int = 0
    removed_segments: int = 0
    modified_segments: int = 0


class DocumentComparator:
    """Compare original documents with converted Markdown."""

    def __init__(self) -> None:
        """Initialize document comparator."""
        self.original_text: str = ""
        self.converted_text: str = ""
        self.original_path: Optional[Path] = None
        self.diff_segments: List[DiffSegment] = []
        self.statistics: Optional[ConversionStatistics] = None

    def load_original(self, file_path: Path) -> bool:
        """
        Load original document.
        
        Args:
            file_path: Path to original document
            
        Returns:
            True if loaded successfully
        """
        try:
            self.original_path = file_path
            ext = file_path.suffix.lower()

            if ext == ".pdf" and HAS_PYMUPDF:
                self.original_text = self._extract_pdf_text(file_path)
            elif ext == ".docx" and HAS_DOCX:
                self.original_text = self._extract_docx_text(file_path)
            elif ext in [".txt", ".md"]:
                with open(file_path, "r", encoding="utf-8") as f:
                    self.original_text = f.read()
            else:
                # Try to read as text
                with open(file_path, "r", encoding="utf-8", errors="ignore") as f:
                    self.original_text = f.read()

            return True
        except Exception as e:
            logger.error(f"Failed to load original document: {e}")
            return False

    def _extract_pdf_text(self, file_path: Path) -> str:
        """
        Extract text from PDF.
        
        Args:
            file_path: Path to PDF file
            
        Returns:
            Extracted text
        """
        if not HAS_PYMUPDF:
            return ""
        
        try:
            doc = fitz.open(str(file_path))
            text_parts = []
            for page in doc:
                text_parts.append(page.get_text())
            doc.close()
            return "\n".join(text_parts)
        except Exception as e:
            logger.error(f"Failed to extract PDF text: {e}")
            return ""

    def _extract_docx_text(self, file_path: Path) -> str:
        """
        Extract text from DOCX.
        
        Args:
            file_path: Path to DOCX file
            
        Returns:
            Extracted text
        """
        if not HAS_DOCX:
            return ""
        
        try:
            doc = Document(str(file_path))
            text_parts = []
            for paragraph in doc.paragraphs:
                text_parts.append(paragraph.text)
            return "\n".join(text_parts)
        except Exception as e:
            logger.error(f"Failed to extract DOCX text: {e}")
            return ""

    def set_converted(self, markdown_text: str) -> None:
        """
        Set converted Markdown text.
        
        Args:
            markdown_text: Converted Markdown text
        """
        self.converted_text = markdown_text

    def compare(self) -> ConversionStatistics:
        """
        Compare original and converted texts.
        
        Returns:
            Conversion statistics
        """
        if not self.original_text or not self.converted_text:
            return ConversionStatistics()

        # Normalize texts for comparison
        original_lines = self.original_text.splitlines(keepends=True)
        converted_lines = self.converted_text.splitlines(keepends=True)

        # Use difflib for comparison
        differ = difflib.Differ()
        diff = list(differ.compare(original_lines, converted_lines))

        # Process diff
        self.diff_segments = []
        line_num = 0
        current_segment: Optional[DiffSegment] = None

        for line in diff:
            if line.startswith("  "):  # Unchanged
                if current_segment:
                    self.diff_segments.append(current_segment)
                    current_segment = None
                self.diff_segments.append(DiffSegment(
                    diff_type=DiffType.UNCHANGED,
                    original_text=line[2:],
                    converted_text=line[2:],
                    line_number=line_num,
                ))
                line_num += 1
            elif line.startswith("- "):  # Removed
                if current_segment and current_segment.diff_type == DiffType.REMOVED:
                    current_segment.original_text += line[2:]
                else:
                    if current_segment:
                        self.diff_segments.append(current_segment)
                    current_segment = DiffSegment(
                        diff_type=DiffType.REMOVED,
                        original_text=line[2:],
                        converted_text="",
                        line_number=line_num,
                    )
            elif line.startswith("+ "):  # Added
                if current_segment and current_segment.diff_type == DiffType.ADDED:
                    current_segment.converted_text += line[2:]
                else:
                    if current_segment:
                        self.diff_segments.append(current_segment)
                    current_segment = DiffSegment(
                        diff_type=DiffType.ADDED,
                        original_text="",
                        converted_text=line[2:],
                        line_number=line_num,
                    )
            elif line.startswith("? "):  # Modified (context)
                if current_segment and current_segment.diff_type in [DiffType.REMOVED, DiffType.ADDED]:
                    current_segment.diff_type = DiffType.MODIFIED

        if current_segment:
            self.diff_segments.append(current_segment)

        # Calculate statistics
        self.statistics = self._calculate_statistics()
        return self.statistics

    def _calculate_statistics(self) -> ConversionStatistics:
        """Calculate conversion statistics."""
        stats = ConversionStatistics()

        stats.total_chars_original = len(self.original_text)
        stats.total_chars_converted = len(self.converted_text)

        for segment in self.diff_segments:
            if segment.diff_type == DiffType.UNCHANGED:
                stats.chars_preserved += len(segment.original_text)
            elif segment.diff_type == DiffType.ADDED:
                stats.chars_added += len(segment.converted_text)
                stats.added_segments += 1
            elif segment.diff_type == DiffType.REMOVED:
                stats.chars_removed += len(segment.original_text)
                stats.removed_segments += 1
            elif segment.diff_type == DiffType.MODIFIED:
                stats.chars_modified += max(len(segment.original_text), len(segment.converted_text))
                stats.modified_segments += 1

        stats.total_differences = stats.added_segments + stats.removed_segments + stats.modified_segments

        # Calculate preservation percentage
        if stats.total_chars_original > 0:
            stats.preservation_percentage = (stats.chars_preserved / stats.total_chars_original) * 100

        # Detect lost elements (simplified)
        stats.elements_lost = self._detect_lost_elements()
        stats.formatting_changed = self._detect_formatting_changes()

        return stats

    def _detect_lost_elements(self) -> List[str]:
        """Detect lost elements in conversion."""
        lost = []

        # Check for images
        if re.search(r'<img[^>]*>', self.original_text, re.IGNORECASE):
            if not re.search(r'!\[.*?\]\(.*?\)', self.converted_text):
                lost.append("Images")

        # Check for tables (simplified)
        if re.search(r'<table[^>]*>', self.original_text, re.IGNORECASE):
            if not re.search(r'\|.*\|', self.converted_text):
                lost.append("Tables")

        # Check for links
        original_links = len(re.findall(r'<a[^>]*href[^>]*>', self.original_text, re.IGNORECASE))
        converted_links = len(re.findall(r'\[.*?\]\(.*?\)', self.converted_text))
        if original_links > converted_links:
            lost.append(f"Links ({original_links - converted_links} lost)")

        return lost

    def _detect_formatting_changes(self) -> List[str]:
        """Detect formatting changes."""
        changes = []

        # Check for bold
        original_bold = len(re.findall(r'<b>|<strong>', self.original_text, re.IGNORECASE))
        converted_bold = len(re.findall(r'\*\*.*?\*\*', self.converted_text))
        if original_bold != converted_bold:
            changes.append("Bold formatting")

        # Check for italic
        original_italic = len(re.findall(r'<i>|<em>', self.original_text, re.IGNORECASE))
        converted_italic = len(re.findall(r'\*.*?\*', self.converted_text))
        if original_italic != converted_italic:
            changes.append("Italic formatting")

        return changes

    def get_diff_segments(self, filter_type: Optional[DiffType] = None) -> List[DiffSegment]:
        """
        Get diff segments, optionally filtered.
        
        Args:
            filter_type: Filter by diff type (None for all)
            
        Returns:
            List of diff segments
        """
        if filter_type is None:
            return self.diff_segments
        return [s for s in self.diff_segments if s.diff_type == filter_type]

    def get_next_difference(self, current_index: int) -> Optional[int]:
        """
        Get next difference index.
        
        Args:
            current_index: Current segment index
            
        Returns:
            Next difference index or None
        """
        for i in range(current_index + 1, len(self.diff_segments)):
            if self.diff_segments[i].diff_type != DiffType.UNCHANGED:
                return i
        return None

    def get_previous_difference(self, current_index: int) -> Optional[int]:
        """
        Get previous difference index.
        
        Args:
            current_index: Current segment index
            
        Returns:
            Previous difference index or None
        """
        for i in range(current_index - 1, -1, -1):
            if self.diff_segments[i].diff_type != DiffType.UNCHANGED:
                return i
        return None

    def export_diff_html(self, output_path: Path) -> bool:
        """
        Export diff as HTML.
        
        Args:
            output_path: Output HTML file path
            
        Returns:
            True if successful
        """
        try:
            html = self._generate_diff_html()
            with open(output_path, "w", encoding="utf-8") as f:
                f.write(html)
            return True
        except Exception as e:
            logger.error(f"Failed to export diff HTML: {e}")
            return False

    def _generate_diff_html(self) -> str:
        """Generate HTML for diff visualization."""
        html_parts = [
            """<!DOCTYPE html>
<html>
<head>
    <meta charset="UTF-8">
    <title>Document Comparison</title>
    <style>
        body { font-family: monospace; margin: 20px; }
        .diff-container { display: flex; }
        .diff-pane { flex: 1; padding: 10px; }
        .original { background-color: #f5f5f5; }
        .converted { background-color: #f5f5f5; }
        .unchanged { background-color: white; }
        .added { background-color: #d4edda; color: #155724; }
        .removed { background-color: #f8d7da; color: #721c24; }
        .modified { background-color: #fff3cd; color: #856404; }
        .line { padding: 2px 5px; margin: 1px 0; }
        .stats { margin: 20px 0; padding: 10px; background-color: #e9ecef; }
    </style>
</head>
<body>
    <h1>Document Comparison</h1>
"""
        ]

        # Statistics
        if self.statistics:
            html_parts.append(f"""
    <div class="stats">
        <h2>Statistics</h2>
        <p>Preservation: {self.statistics.preservation_percentage:.1f}%</p>
        <p>Added: {self.statistics.chars_added} chars</p>
        <p>Removed: {self.statistics.chars_removed} chars</p>
        <p>Modified: {self.statistics.chars_modified} chars</p>
        <p>Total Differences: {self.statistics.total_differences}</p>
    </div>
""")

        # Diff view
        html_parts.append("""
    <div class="diff-container">
        <div class="diff-pane original">
            <h2>Original</h2>
""")

        for segment in self.diff_segments:
            css_class = segment.diff_type.value
            text = segment.original_text.replace("<", "&lt;").replace(">", "&gt;")
            html_parts.append(f'<div class="line {css_class}">{text}</div>')

        html_parts.append("""
        </div>
        <div class="diff-pane converted">
            <h2>Converted</h2>
""")

        for segment in self.diff_segments:
            css_class = segment.diff_type.value
            text = segment.converted_text.replace("<", "&lt;").replace(">", "&gt;")
            html_parts.append(f'<div class="line {css_class}">{text}</div>')

        html_parts.append("""
        </div>
    </div>
</body>
</html>
""")

        return "\n".join(html_parts)

