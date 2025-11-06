"""
OCR Plugin for MarkItDown GUI.

This plugin provides advanced OCR capabilities using Tesseract.
"""

from pathlib import Path
from typing import Dict, Any, Optional
import logging

try:
    import pytesseract
    from PIL import Image
    HAS_TESSERACT = True
except ImportError:
    HAS_TESSERACT = False

from gui.core.plugin_system import (
    AbstractPlugin,
    PluginMetadata,
    PluginType,
    PluginStatus,
)

logger = logging.getLogger(__name__)

PLUGIN_METADATA = PluginMetadata(
    plugin_id="ocr_advanced",
    name="Advanced OCR",
    version="1.0.0",
    description="Advanced OCR using Tesseract for image and PDF text extraction",
    author="MarkItDown Team",
    plugin_type=PluginType.INPUT_PROCESSOR,
    dependencies=[],
    config_schema={
        "tesseract_path": {"type": "string", "default": ""},
        "language": {"type": "string", "default": "eng"},
        "psm_mode": {"type": "integer", "default": 6},
    },
    permissions=["file_read", "image_processing"],
)


class OCRPlugin(AbstractPlugin):
    """OCR plugin using Tesseract."""

    def __init__(self, plugin_id: str, metadata: PluginMetadata) -> None:
        """Initialize OCR plugin."""
        super().__init__(plugin_id, metadata)
        self.tesseract_available = HAS_TESSERACT

    def init(self, context: Dict[str, Any]) -> None:
        """Initialize plugin."""
        if not self.tesseract_available:
            self.logger.warning("Tesseract not available")
            return

        # Configure tesseract path if provided
        tesseract_path = self.config.get("tesseract_path", "")
        if tesseract_path:
            pytesseract.pytesseract.tesseract_cmd = tesseract_path

        self.logger.info("OCR plugin initialized")

    def activate(self) -> None:
        """Activate plugin."""
        if not self.tesseract_available:
            raise RuntimeError("Tesseract not available")

        self.status = PluginStatus.ACTIVATED
        self.logger.info("OCR plugin activated")

    def deactivate(self) -> None:
        """Deactivate plugin."""
        self.status = PluginStatus.DEACTIVATED
        self.logger.info("OCR plugin deactivated")

    def extract_text_from_image(self, image_path: Path) -> str:
        """
        Extract text from image using OCR.
        
        Args:
            image_path: Path to image file
            
        Returns:
            Extracted text
        """
        if not self.tesseract_available:
            return ""

        try:
            image = Image.open(image_path)
            language = self.config.get("language", "eng")
            psm_mode = self.config.get("psm_mode", 6)

            custom_config = f"--psm {psm_mode} -l {language}"
            text = pytesseract.image_to_string(image, config=custom_config)
            return text
        except Exception as e:
            self.logger.error(f"Error extracting text from image: {e}")
            return ""

    def extract_text_from_pdf_page(self, pdf_path: Path, page_num: int) -> str:
        """
        Extract text from PDF page using OCR.
        
        Args:
            pdf_path: Path to PDF file
            page_num: Page number (0-indexed)
            
        Returns:
            Extracted text
        """
        if not self.tesseract_available:
            return ""

        try:
            import fitz  # PyMuPDF
            doc = fitz.open(str(pdf_path))
            page = doc[page_num]
            pix = page.get_pixmap()
            img_data = pix.tobytes("ppm")

            from io import BytesIO
            image = Image.open(BytesIO(img_data))
            language = self.config.get("language", "eng")
            text = pytesseract.image_to_string(image, lang=language)
            doc.close()
            return text
        except Exception as e:
            self.logger.error(f"Error extracting text from PDF: {e}")
            return ""

