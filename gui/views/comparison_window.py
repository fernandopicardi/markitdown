"""
Document comparison window for MarkItDown GUI.

Features:
- Side-by-side comparison
- Visual diff with colors
- Navigation between differences
- Conversion statistics
- PDF/DOCX viewers
- Synchronized zoom
- Export diff HTML
- Spotlight mode
- Diff filters
"""

import customtkinter as ctk
from tkinter import filedialog, messagebox
from pathlib import Path
from typing import Optional
import logging

from gui.core.document_comparator import DocumentComparator, DiffType
from gui.components.document_viewer import PDFViewer, DOCXViewer
from gui.components.diff_viewer import DiffViewer, StatisticsPanel

logger = logging.getLogger(__name__)


class DocumentComparisonWindow(ctk.CTk):
    """Main window for document comparison."""

    def __init__(
        self,
        original_path: Optional[Path] = None,
        converted_text: str = "",
        **kwargs
    ) -> None:
        """
        Initialize comparison window.
        
        Args:
            original_path: Path to original document
            converted_text: Converted Markdown text
            **kwargs: Additional CTk arguments
        """
        super().__init__(**kwargs)
        self.original_path = original_path
        self.converted_text = converted_text
        self.comparator = DocumentComparator()
        self.zoom_level = 1.0

        self._setup_window()
        self._create_layout()
        self._load_documents()

        logger.info("Document comparison window initialized")

    def _setup_window(self) -> None:
        """Configure window properties."""
        self.title("MarkItDown - Document Comparison")
        self.geometry("1600x1000")
        self.minsize(1400, 800)

    def _create_layout(self) -> None:
        """Create main layout."""
        # Top toolbar
        toolbar = ctk.CTkFrame(self)
        toolbar.pack(fill="x", padx=10, pady=10)

        # Left: File operations
        left_toolbar = ctk.CTkFrame(toolbar)
        left_toolbar.pack(side="left", padx=5)

        ctk.CTkButton(
            left_toolbar,
            text="Load Original",
            command=self._load_original,
            width=120,
        ).pack(side="left", padx=2)

        ctk.CTkButton(
            left_toolbar,
            text="Load Converted",
            command=self._load_converted,
            width=120,
        ).pack(side="left", padx=2)

        ctk.CTkButton(
            left_toolbar,
            text="Compare",
            command=self._compare_documents,
            width=100,
        ).pack(side="left", padx=2)

        # Center: View mode
        center_toolbar = ctk.CTkFrame(toolbar)
        center_toolbar.pack(side="left", padx=20)

        ctk.CTkLabel(center_toolbar, text="View:").pack(side="left", padx=5)
        self.view_mode_var = ctk.StringVar(value="diff")
        view_menu = ctk.CTkOptionMenu(
            center_toolbar,
            values=["diff", "original", "converted", "side-by-side"],
            variable=self.view_mode_var,
            command=self._change_view_mode,
            width=150,
        )
        view_menu.pack(side="left", padx=5)

        # Right: Export and zoom
        right_toolbar = ctk.CTkFrame(toolbar)
        right_toolbar.pack(side="right", padx=5)

        # Zoom controls
        ctk.CTkLabel(right_toolbar, text="Zoom:").pack(side="left", padx=5)
        ctk.CTkButton(
            right_toolbar,
            text="-",
            command=self._zoom_out,
            width=30,
        ).pack(side="left", padx=2)

        self.zoom_label = ctk.CTkLabel(right_toolbar, text="100%")
        self.zoom_label.pack(side="left", padx=5)

        ctk.CTkButton(
            right_toolbar,
            text="+",
            command=self._zoom_in,
            width=30,
        ).pack(side="left", padx=2)

        ctk.CTkButton(
            right_toolbar,
            text="Export Diff HTML",
            command=self._export_diff,
            width=120,
        ).pack(side="left", padx=5)

        # Main content area
        self.content_frame = ctk.CTkFrame(self)
        self.content_frame.pack(fill="both", expand=True, padx=10, pady=10)

        # Create tab view
        self.tabs = ctk.CTkTabview(self.content_frame)
        self.tabs.pack(fill="both", expand=True)

        # Diff tab
        diff_tab = self.tabs.add("Diff View")
        self._create_diff_view(diff_tab)

        # Statistics tab
        stats_tab = self.tabs.add("Statistics")
        self._create_statistics_view(stats_tab)

        # Original tab
        original_tab = self.tabs.add("Original")
        self._create_original_view(original_tab)

        # Converted tab
        converted_tab = self.tabs.add("Converted")
        self._create_converted_view(converted_tab)

    def _create_diff_view(self, parent: ctk.CTkFrame) -> None:
        """Create diff view."""
        self.diff_viewer = DiffViewer(
            parent,
            self.comparator,
            on_navigate=self._on_navigate_diff,
        )
        self.diff_viewer.pack(fill="both", expand=True)

    def _create_statistics_view(self, parent: ctk.CTkFrame) -> None:
        """Create statistics view."""
        self.stats_panel = StatisticsPanel(parent)
        self.stats_panel.pack(fill="both", expand=True, padx=10, pady=10)

    def _create_original_view(self, parent: ctk.CTkFrame) -> None:
        """Create original document view."""
        # Check file type and use appropriate viewer
        if self.original_path:
            ext = self.original_path.suffix.lower()
            if ext == ".pdf":
                self.original_viewer = PDFViewer(parent)
            elif ext == ".docx":
                self.original_viewer = DOCXViewer(parent)
            else:
                # Text viewer
                self.original_viewer = ctk.CTkTextbox(
                    parent,
                    wrap="word",
                    font=ctk.CTkFont(family="Consolas", size=11),
                )
            self.original_viewer.pack(fill="both", expand=True, padx=5, pady=5)
        else:
            label = ctk.CTkLabel(
                parent,
                text="No original document loaded",
                font=ctk.CTkFont(size=12),
            )
            label.pack(expand=True)

    def _create_converted_view(self, parent: ctk.CTkFrame) -> None:
        """Create converted document view."""
        self.converted_viewer = ctk.CTkTextbox(
            parent,
            wrap="word",
            font=ctk.CTkFont(family="Consolas", size=11),
        )
        self.converted_viewer.pack(fill="both", expand=True, padx=5, pady=5)
        if self.converted_text:
            self.converted_viewer.insert("1.0", self.converted_text)

    def _load_documents(self) -> None:
        """Load documents."""
        if self.original_path:
            self.comparator.load_original(self.original_path)
            self._load_original_viewer()

        if self.converted_text:
            self.comparator.set_converted(self.converted_text)

    def _load_original_viewer(self) -> None:
        """Load original document in viewer."""
        if not self.original_path:
            return

        # Find original tab and update viewer
        for tab_name in self.tabs._tab_dict:
            if tab_name == "Original":
                # Clear and recreate
                original_tab = self.tabs._tab_dict[tab_name]
                for widget in original_tab.winfo_children():
                    widget.destroy()

                ext = self.original_path.suffix.lower()
                if ext == ".pdf":
                    viewer = PDFViewer(original_tab)
                    viewer.load_pdf(self.original_path)
                elif ext == ".docx":
                    viewer = DOCXViewer(original_tab)
                    viewer.load_docx(self.original_path)
                else:
                    viewer = ctk.CTkTextbox(
                        original_tab,
                        wrap="word",
                        font=ctk.CTkFont(family="Consolas", size=11),
                    )
                    with open(self.original_path, "r", encoding="utf-8", errors="ignore") as f:
                        viewer.insert("1.0", f.read())

                viewer.pack(fill="both", expand=True, padx=5, pady=5)
                break

    def _load_original(self) -> None:
        """Load original document."""
        file_path = filedialog.askopenfilename(
            title="Load Original Document",
            filetypes=[
                ("All Supported", "*.pdf;*.docx;*.txt;*.md"),
                ("PDF", "*.pdf"),
                ("Word", "*.docx"),
                ("Text", "*.txt;*.md"),
                ("All Files", "*.*")
            ]
        )
        if file_path:
            self.original_path = Path(file_path)
            if self.comparator.load_original(self.original_path):
                self._load_original_viewer()
                messagebox.showinfo("Success", "Original document loaded!")
            else:
                messagebox.showerror("Error", "Failed to load original document")

    def _load_converted(self) -> None:
        """Load converted Markdown."""
        file_path = filedialog.askopenfilename(
            title="Load Converted Markdown",
            filetypes=[("Markdown", "*.md"), ("Text", "*.txt"), ("All Files", "*.*")]
        )
        if file_path:
            try:
                with open(file_path, "r", encoding="utf-8") as f:
                    content = f.read()
                self.converted_text = content
                self.comparator.set_converted(content)
                self.converted_viewer.delete("1.0", "end")
                self.converted_viewer.insert("1.0", content)
                messagebox.showinfo("Success", "Converted document loaded!")
            except Exception as e:
                messagebox.showerror("Error", f"Failed to load converted document: {e}")

    def _compare_documents(self) -> None:
        """Compare documents."""
        if not self.comparator.original_text:
            messagebox.showwarning("Warning", "Please load original document first")
            return

        if not self.comparator.converted_text:
            messagebox.showwarning("Warning", "Please load converted document first")
            return

        # Perform comparison
        stats = self.comparator.compare()

        # Update views
        self.diff_viewer._update_display()
        self.stats_panel.update_statistics(stats)

        # Switch to diff tab
        self.tabs.set("Diff View")

        messagebox.showinfo(
            "Comparison Complete",
            f"Comparison complete!\n\n"
            f"Preservation: {stats.preservation_percentage:.1f}%\n"
            f"Total Differences: {stats.total_differences}"
        )

    def _change_view_mode(self, mode: str) -> None:
        """Change view mode."""
        # View mode switching is handled by tabs
        pass

    def _zoom_in(self) -> None:
        """Zoom in."""
        self.zoom_level = min(self.zoom_level + 0.1, 2.0)
        self._update_zoom()

    def _zoom_out(self) -> None:
        """Zoom out."""
        self.zoom_level = max(self.zoom_level - 0.1, 0.5)
        self._update_zoom()

    def _update_zoom(self) -> None:
        """Update zoom level."""
        self.zoom_label.configure(text=f"{int(self.zoom_level * 100)}%")
        # Apply zoom to viewers
        if hasattr(self, 'original_viewer') and hasattr(self.original_viewer, 'set_zoom'):
            self.original_viewer.set_zoom(self.zoom_level)

    def _on_navigate_diff(self, index: int) -> None:
        """Handle diff navigation."""
        # Scroll to difference
        pass

    def _export_diff(self) -> None:
        """Export diff as HTML."""
        if not self.comparator.diff_segments:
            messagebox.showwarning("Warning", "Please compare documents first")
            return

        file_path = filedialog.asksaveasfilename(
            title="Export Diff HTML",
            defaultextension=".html",
            filetypes=[("HTML", "*.html"), ("All Files", "*.*")]
        )
        if file_path:
            if self.comparator.export_diff_html(Path(file_path)):
                messagebox.showinfo("Success", "Diff HTML exported successfully!")
            else:
                messagebox.showerror("Error", "Failed to export diff HTML")

    def run(self) -> None:
        """Start the window."""
        logger.info("Starting document comparison window")
        self.mainloop()


def show_comparison(original_path: Optional[Path] = None, converted_text: str = "") -> None:
    """
    Show document comparison window.
    
    Args:
        original_path: Path to original document
        converted_text: Converted Markdown text
    """
    window = DocumentComparisonWindow(
        original_path=original_path,
        converted_text=converted_text,
    )
    window.run()

