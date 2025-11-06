"""
Visual diff viewer component with side-by-side comparison.
"""

import customtkinter as ctk
from typing import Optional, List, Callable
import logging

from gui.core.document_comparator import (
    DocumentComparator,
    DiffSegment,
    DiffType,
    ConversionStatistics,
)

logger = logging.getLogger(__name__)


class DiffViewer(ctk.CTkFrame):
    """Visual diff viewer with side-by-side comparison."""

    def __init__(
        self,
        master: Any,
        comparator: DocumentComparator,
        on_navigate: Optional[Callable[[int], None]] = None,
        **kwargs
    ) -> None:
        """
        Initialize diff viewer.
        
        Args:
            master: Parent widget
            comparator: DocumentComparator instance
            on_navigate: Callback for navigation
            **kwargs: Additional CTkFrame arguments
        """
        super().__init__(master, **kwargs)
        self.comparator = comparator
        self.on_navigate = on_navigate
        self.current_diff_index = 0
        self.spotlight_mode = False
        self.filter_type: Optional[DiffType] = None

        self._create_widgets()
        self._update_display()

    def _create_widgets(self) -> None:
        """Create diff viewer widgets."""
        # Toolbar
        toolbar = ctk.CTkFrame(self)
        toolbar.pack(fill="x", padx=5, pady=5)

        # Navigation
        nav_frame = ctk.CTkFrame(toolbar)
        nav_frame.pack(side="left", padx=5)

        ctk.CTkButton(
            nav_frame,
            text="◀ Previous",
            command=self._prev_diff,
            width=100,
        ).pack(side="left", padx=2)

        self.diff_label = ctk.CTkLabel(nav_frame, text="Diff: 0/0")
        self.diff_label.pack(side="left", padx=10)

        ctk.CTkButton(
            nav_frame,
            text="Next ▶",
            command=self._next_diff,
            width=100,
        ).pack(side="left", padx=2)

        # Filters
        filter_frame = ctk.CTkFrame(toolbar)
        filter_frame.pack(side="right", padx=5)

        ctk.CTkLabel(filter_frame, text="Filter:").pack(side="left", padx=5)
        self.filter_var = ctk.StringVar(value="all")
        filter_menu = ctk.CTkOptionMenu(
            filter_frame,
            values=["all", "added", "removed", "modified"],
            variable=self.filter_var,
            command=self._change_filter,
            width=120,
        )
        filter_menu.pack(side="left", padx=5)

        # Spotlight mode
        self.spotlight_var = ctk.BooleanVar(value=False)
        spotlight_check = ctk.CTkCheckBox(
            filter_frame,
            text="Spotlight",
            variable=self.spotlight_var,
            command=self._toggle_spotlight,
        )
        spotlight_check.pack(side="left", padx=5)

        # Main diff view
        diff_container = ctk.CTkFrame(self)
        diff_container.pack(fill="both", expand=True, padx=5, pady=5)

        # Left: Original
        left_frame = ctk.CTkFrame(diff_container)
        left_frame.pack(side="left", fill="both", expand=True, padx=5)

        ctk.CTkLabel(
            left_frame,
            text="Original Document",
            font=ctk.CTkFont(size=12, weight="bold"),
        ).pack(pady=5)

        self.original_text = ctk.CTkTextbox(
            left_frame,
            wrap="word",
            font=ctk.CTkFont(family="Consolas", size=10),
        )
        self.original_text.pack(fill="both", expand=True, padx=5, pady=5)

        # Right: Converted
        right_frame = ctk.CTkFrame(diff_container)
        right_frame.pack(side="right", fill="both", expand=True, padx=5)

        ctk.CTkLabel(
            right_frame,
            text="Converted Markdown",
            font=ctk.CTkFont(size=12, weight="bold"),
        ).pack(pady=5)

        self.converted_text = ctk.CTkTextbox(
            right_frame,
            wrap="word",
            font=ctk.CTkFont(family="Consolas", size=10),
        )
        self.converted_text.pack(fill="both", expand=True, padx=5, pady=5)

    def _update_display(self) -> None:
        """Update diff display."""
        segments = self.comparator.get_diff_segments(self.filter_type)

        if not segments:
            self.original_text.delete("1.0", "end")
            self.converted_text.delete("1.0", "end")
            return

        # Build text with colors
        original_parts = []
        converted_parts = []

        for i, segment in enumerate(segments):
            if self.spotlight_mode and segment.diff_type == DiffType.UNCHANGED:
                # Skip unchanged in spotlight mode
                continue

            # Color tags (simplified - CTkTextbox doesn't support colors directly)
            # We'll use text markers instead
            orig_marker = self._get_marker(segment.diff_type, "original")
            conv_marker = self._get_marker(segment.diff_type, "converted")

            original_parts.append(f"{orig_marker}{segment.original_text}")
            converted_parts.append(f"{conv_marker}{segment.converted_text}")

        # Update text widgets
        self.original_text.delete("1.0", "end")
        self.original_text.insert("1.0", "".join(original_parts))

        self.converted_text.delete("1.0", "end")
        self.converted_text.insert("1.0", "".join(converted_parts))

        # Update navigation label
        diff_count = len([s for s in segments if s.diff_type != DiffType.UNCHANGED])
        self.diff_label.configure(text=f"Diff: {self.current_diff_index + 1}/{diff_count}")

    def _get_marker(self, diff_type: DiffType, side: str) -> str:
        """Get text marker for diff type."""
        markers = {
            DiffType.ADDED: "[+] " if side == "converted" else "[ ] ",
            DiffType.REMOVED: "[ ] " if side == "original" else "[-] ",
            DiffType.MODIFIED: "[~] ",
            DiffType.UNCHANGED: "    ",
        }
        return markers.get(diff_type, "")

    def _prev_diff(self) -> None:
        """Navigate to previous difference."""
        segments = self.comparator.get_diff_segments(self.filter_type)
        diff_indices = [i for i, s in enumerate(segments) if s.diff_type != DiffType.UNCHANGED]

        if diff_indices:
            current_pos = diff_indices.index(self.current_diff_index) if self.current_diff_index in diff_indices else 0
            if current_pos > 0:
                self.current_diff_index = diff_indices[current_pos - 1]
                self._update_display()
                if self.on_navigate:
                    self.on_navigate(self.current_diff_index)

    def _next_diff(self) -> None:
        """Navigate to next difference."""
        segments = self.comparator.get_diff_segments(self.filter_type)
        diff_indices = [i for i, s in enumerate(segments) if s.diff_type != DiffType.UNCHANGED]

        if diff_indices:
            current_pos = diff_indices.index(self.current_diff_index) if self.current_diff_index in diff_indices else 0
            if current_pos < len(diff_indices) - 1:
                self.current_diff_index = diff_indices[current_pos + 1]
                self._update_display()
                if self.on_navigate:
                    self.on_navigate(self.current_diff_index)

    def _change_filter(self, filter_name: str) -> None:
        """Change diff filter."""
        filter_map = {
            "all": None,
            "added": DiffType.ADDED,
            "removed": DiffType.REMOVED,
            "modified": DiffType.MODIFIED,
        }
        self.filter_type = filter_map.get(filter_name)
        self.current_diff_index = 0
        self._update_display()

    def _toggle_spotlight(self) -> None:
        """Toggle spotlight mode."""
        self.spotlight_mode = self.spotlight_var.get()
        self._update_display()


class StatisticsPanel(ctk.CTkFrame):
    """Statistics panel for conversion."""

    def __init__(self, master: Any, **kwargs) -> None:
        """
        Initialize statistics panel.
        
        Args:
            master: Parent widget
            **kwargs: Additional CTkFrame arguments
        """
        super().__init__(master, **kwargs)
        self.statistics: Optional[ConversionStatistics] = None
        self._create_widgets()

    def _create_widgets(self) -> None:
        """Create statistics widgets."""
        ctk.CTkLabel(
            self,
            text="Conversion Statistics",
            font=ctk.CTkFont(size=14, weight="bold"),
        ).pack(pady=10)

        self.stats_text = ctk.CTkTextbox(
            self,
            wrap="word",
            font=ctk.CTkFont(size=11),
            height=300,
        )
        self.stats_text.pack(fill="both", expand=True, padx=10, pady=10)

    def update_statistics(self, stats: ConversionStatistics) -> None:
        """
        Update statistics display.
        
        Args:
            stats: Conversion statistics
        """
        self.statistics = stats
        self.stats_text.delete("1.0", "end")

        text = f"""Preservation: {stats.preservation_percentage:.1f}%

Original Size: {stats.total_chars_original:,} characters
Converted Size: {stats.total_chars_converted:,} characters

Preserved: {stats.chars_preserved:,} characters
Added: {stats.chars_added:,} characters
Removed: {stats.chars_removed:,} characters
Modified: {stats.chars_modified:,} characters

Total Differences: {stats.total_differences}
  - Added segments: {stats.added_segments}
  - Removed segments: {stats.removed_segments}
  - Modified segments: {stats.modified_segments}
"""

        if stats.elements_lost:
            text += f"\nElements Lost:\n"
            for element in stats.elements_lost:
                text += f"  - {element}\n"

        if stats.formatting_changed:
            text += f"\nFormatting Changed:\n"
            for change in stats.formatting_changed:
                text += f"  - {change}\n"

        self.stats_text.insert("1.0", text)

