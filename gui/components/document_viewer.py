"""
Document viewer components for PDF and DOCX.
"""

import customtkinter as ctk
from pathlib import Path
from typing import Optional, Callable
import logging

try:
    import fitz  # PyMuPDF
    from PIL import Image, ImageTk
    HAS_PYMUPDF = True
except ImportError:
    HAS_PYMUPDF = False

try:
    from docx import Document
    HAS_DOCX = True
except ImportError:
    HAS_DOCX = False

logger = logging.getLogger(__name__)


class PDFViewer(ctk.CTkFrame):
    """PDF viewer using PyMuPDF."""

    def __init__(self, master: Any, **kwargs) -> None:
        """
        Initialize PDF viewer.
        
        Args:
            master: Parent widget
            **kwargs: Additional CTkFrame arguments
        """
        super().__init__(master, **kwargs)
        self.pdf_path: Optional[Path] = None
        self.doc = None
        self.current_page = 0
        self.zoom_level = 1.0
        self.page_images = []

        if not HAS_PYMUPDF:
            self._create_error_widget("PyMuPDF not available")
            return

        self._create_widgets()

    def _create_error_widget(self, message: str) -> None:
        """Create error widget."""
        error_label = ctk.CTkLabel(
            self,
            text=message,
            font=ctk.CTkFont(size=12),
        )
        error_label.pack(expand=True)

    def _create_widgets(self) -> None:
        """Create viewer widgets."""
        # Toolbar
        toolbar = ctk.CTkFrame(self)
        toolbar.pack(fill="x", padx=5, pady=5)

        self.page_label = ctk.CTkLabel(toolbar, text="Page: 0/0")
        self.page_label.pack(side="left", padx=10)

        ctk.CTkButton(
            toolbar,
            text="◀",
            command=self._prev_page,
            width=40,
        ).pack(side="left", padx=2)

        ctk.CTkButton(
            toolbar,
            text="▶",
            command=self._next_page,
            width=40,
        ).pack(side="left", padx=2)

        # Zoom controls
        ctk.CTkLabel(toolbar, text="Zoom:").pack(side="left", padx=10)
        ctk.CTkButton(
            toolbar,
            text="-",
            command=self._zoom_out,
            width=30,
        ).pack(side="left", padx=2)

        self.zoom_label = ctk.CTkLabel(toolbar, text="100%")
        self.zoom_label.pack(side="left", padx=5)

        ctk.CTkButton(
            toolbar,
            text="+",
            command=self._zoom_in,
            width=30,
        ).pack(side="left", padx=2)

        # Canvas for PDF display
        self.canvas_frame = ctk.CTkFrame(self)
        self.canvas_frame.pack(fill="both", expand=True, padx=5, pady=5)

        # Use scrollable frame
        self.scrollable = ctk.CTkScrollableFrame(self.canvas_frame)
        self.scrollable.pack(fill="both", expand=True)

        self.image_label = ctk.CTkLabel(self.scrollable, text="")
        self.image_label.pack()

    def load_pdf(self, pdf_path: Path) -> bool:
        """
        Load PDF file.
        
        Args:
            pdf_path: Path to PDF file
            
        Returns:
            True if loaded successfully
        """
        try:
            self.pdf_path = pdf_path
            self.doc = fitz.open(str(pdf_path))
            self.current_page = 0
            self.page_images = []
            self._render_page()
            return True
        except Exception as e:
            logger.error(f"Failed to load PDF: {e}")
            return False

    def _render_page(self) -> None:
        """Render current page."""
        if not self.doc:
            return

        try:
            page = self.doc[self.current_page]
            zoom_matrix = fitz.Matrix(self.zoom_level, self.zoom_level)
            pix = page.get_pixmap(matrix=zoom_matrix)
            img_data = pix.tobytes("ppm")

            # Convert to PIL Image
            import io
            img = Image.open(io.BytesIO(img_data))
            photo = ImageTk.PhotoImage(img)

            self.image_label.configure(image=photo)
            self.image_label.image = photo  # Keep reference

            # Update page label
            self.page_label.configure(text=f"Page: {self.current_page + 1}/{len(self.doc)}")
        except Exception as e:
            logger.error(f"Failed to render PDF page: {e}")

    def _prev_page(self) -> None:
        """Go to previous page."""
        if self.doc and self.current_page > 0:
            self.current_page -= 1
            self._render_page()

    def _next_page(self) -> None:
        """Go to next page."""
        if self.doc and self.current_page < len(self.doc) - 1:
            self.current_page += 1
            self._render_page()

    def _zoom_in(self) -> None:
        """Zoom in."""
        self.zoom_level = min(self.zoom_level + 0.2, 3.0)
        self.zoom_label.configure(text=f"{int(self.zoom_level * 100)}%")
        self._render_page()

    def _zoom_out(self) -> None:
        """Zoom out."""
        self.zoom_level = max(self.zoom_level - 0.2, 0.5)
        self.zoom_label.configure(text=f"{int(self.zoom_level * 100)}%")
        self._render_page()

    def set_zoom(self, zoom: float) -> None:
        """
        Set zoom level.
        
        Args:
            zoom: Zoom level (0.5-3.0)
        """
        self.zoom_level = max(0.5, min(3.0, zoom))
        self.zoom_label.configure(text=f"{int(self.zoom_level * 100)}%")
        self._render_page()


class DOCXViewer(ctk.CTkFrame):
    """DOCX viewer using python-docx."""

    def __init__(self, master: Any, **kwargs) -> None:
        """
        Initialize DOCX viewer.
        
        Args:
            master: Parent widget
            **kwargs: Additional CTkFrame arguments
        """
        super().__init__(master, **kwargs)
        self.docx_path: Optional[Path] = None
        self.doc = None
        self.zoom_level = 1.0

        if not HAS_DOCX:
            self._create_error_widget("python-docx not available")
            return

        self._create_widgets()

    def _create_error_widget(self, message: str) -> None:
        """Create error widget."""
        error_label = ctk.CTkLabel(
            self,
            text=message,
            font=ctk.CTkFont(size=12),
        )
        error_label.pack(expand=True)

    def _create_widgets(self) -> None:
        """Create viewer widgets."""
        # Toolbar
        toolbar = ctk.CTkFrame(self)
        toolbar.pack(fill="x", padx=5, pady=5)

        # Zoom controls
        ctk.CTkLabel(toolbar, text="Zoom:").pack(side="left", padx=10)
        ctk.CTkButton(
            toolbar,
            text="-",
            command=self._zoom_out,
            width=30,
        ).pack(side="left", padx=2)

        self.zoom_label = ctk.CTkLabel(toolbar, text="100%")
        self.zoom_label.pack(side="left", padx=5)

        ctk.CTkButton(
            toolbar,
            text="+",
            command=self._zoom_in,
            width=30,
        ).pack(side="left", padx=2)

        # Text display
        self.text_widget = ctk.CTkTextbox(
            self,
            wrap="word",
            font=ctk.CTkFont(size=11),
        )
        self.text_widget.pack(fill="both", expand=True, padx=5, pady=5)

    def load_docx(self, docx_path: Path) -> bool:
        """
        Load DOCX file.
        
        Args:
            docx_path: Path to DOCX file
            
        Returns:
            True if loaded successfully
        """
        try:
            self.docx_path = docx_path
            self.doc = Document(str(docx_path))
            self._render_document()
            return True
        except Exception as e:
            logger.error(f"Failed to load DOCX: {e}")
            return False

    def _render_document(self) -> None:
        """Render DOCX document."""
        if not self.doc:
            return

        self.text_widget.delete("1.0", "end")

        for paragraph in self.doc.paragraphs:
            text = paragraph.text
            if text.strip():
                self.text_widget.insert("end", text + "\n\n")

    def _zoom_in(self) -> None:
        """Zoom in."""
        self.zoom_level = min(self.zoom_level + 0.1, 2.0)
        self._update_font_size()

    def _zoom_out(self) -> None:
        """Zoom out."""
        self.zoom_level = max(self.zoom_level - 0.1, 0.5)
        self._update_font_size()

    def _update_font_size(self) -> None:
        """Update font size based on zoom."""
        base_size = 11
        new_size = int(base_size * self.zoom_level)
        self.text_widget.configure(font=ctk.CTkFont(size=new_size))
        self.zoom_label.configure(text=f"{int(self.zoom_level * 100)}%")

    def set_zoom(self, zoom: float) -> None:
        """
        Set zoom level.
        
        Args:
            zoom: Zoom level (0.5-2.0)
        """
        self.zoom_level = max(0.5, min(2.0, zoom))
        self._update_font_size()

