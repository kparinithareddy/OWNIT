import os
import io
import re
import logging
from typing import Tuple, List, Dict, Any, Optional
from PIL import Image, ImageEnhance, ImageFilter
import pytesseract
import pymupdf

from app.core.config import settings

logger = logging.getLogger("ownit.core.ocr_engine")

if os.path.exists(settings.TESSERACT_CMD_PATH):
    pytesseract.pytesseract.tesseract_cmd = settings.TESSERACT_CMD_PATH


class OCREngine:
    """
    Core engine for Optical Character Recognition and document text extraction.
    Handles image preprocessing (grayscale, contrast, sharpening) and multi-page PDFs.
    """
    @classmethod
    def is_tesseract_available(cls) -> bool:
        try:
            pytesseract.get_tesseract_version()
            return True
        except Exception as exc:
            logger.warning(f"Tesseract OCR is not accessible: {exc}")
            return False

    @classmethod
    def preprocess_image(cls, image: Image.Image) -> Image.Image:
        try:
            if image.mode in ("RGBA", "LA", "P"):
                background = Image.new("RGB", image.size, (255, 255, 255))
                if image.mode == "RGBA":
                    background.paste(image, mask=image.split()[3])
                else:
                    background.paste(image)
                image = background

            gray = image.convert("L")
            width, height = gray.size
            if width < 1200 and height < 1200:
                scale_factor = max(1.5, 1200.0 / max(width, 1))
                new_size = (int(width * scale_factor), int(height * scale_factor))
                gray = gray.resize(new_size, Image.Resampling.LANCZOS)

            enhancer = ImageEnhance.Contrast(gray)
            enhanced = enhancer.enhance(1.8)
            sharpened = enhanced.filter(ImageFilter.SHARPEN)
            return sharpened
        except Exception as exc:
            logger.warning(f"Image preprocessing error, continuing with original: {exc}")
            return image

    @classmethod
    def extract_text_from_image_bytes(cls, image_bytes: bytes) -> Tuple[str, Dict[str, Any]]:
        metadata = {"pageCount": 1, "ocrEngine": "tesseract"}
        try:
            image = Image.open(io.BytesIO(image_bytes))
            metadata["originalSize"] = list(image.size)
            metadata["originalMode"] = image.mode

            # Try multi-pass extraction (PSM 3 default, PSM 6 uniform, PSM 11 sparse)
            best_text = ""
            
            # Pass 1: Raw image with auto page segmentation
            try:
                raw_text = pytesseract.image_to_string(image, config=r"--oem 3 --psm 3").strip()
                if len(raw_text) > len(best_text):
                    best_text = raw_text
            except Exception:
                pass

            # Pass 2: Preprocessed (scaled, enhanced contrast) with PSM 6
            processed = cls.preprocess_image(image)
            try:
                p_text = pytesseract.image_to_string(processed, config=r"--oem 3 --psm 6").strip()
                if len(p_text) > len(best_text):
                    best_text = p_text
            except Exception:
                pass

            # Pass 3: Preprocessed with default config
            if len(best_text) < 30:
                try:
                    p3_text = pytesseract.image_to_string(processed).strip()
                    if len(p3_text) > len(best_text):
                        best_text = p3_text
                except Exception:
                    pass

            return best_text.strip(), metadata
        except Exception as exc:
            logger.error(f"Failed to extract text from image: {exc}")
            raise

    @classmethod
    def extract_text_from_pdf_bytes(cls, pdf_bytes: bytes, max_pages: int = 5) -> Tuple[str, Dict[str, Any]]:
        full_text_parts: List[str] = []
        doc = pymupdf.open(stream=pdf_bytes, filetype="pdf")
        total_pages = len(doc)
        pages_to_process = min(total_pages, max_pages)

        metadata = {
            "pageCount": pages_to_process,
            "totalPages": total_pages,
            "ocrEngine": "pymupdf_hybrid"
        }

        for page_idx in range(pages_to_process):
            page = doc.load_page(page_idx)
            text = page.get_text("text").strip()
            if len(text) < 40 and cls.is_tesseract_available():
                logger.info(f"PDF Page {page_idx + 1} appears scanned. Rendering image for OCR...")
                zoom_matrix = pymupdf.Matrix(2.0, 2.0)
                pixmap = page.get_pixmap(matrix=zoom_matrix)
                img_bytes = pixmap.tobytes("png")
                page_text, _ = cls.extract_text_from_image_bytes(img_bytes)
                if page_text:
                    full_text_parts.append(f"--- Page {page_idx + 1} ---\n{page_text}")
            else:
                if text:
                    full_text_parts.append(f"--- Page {page_idx + 1} ---\n{text}")

        combined_text = "\n\n".join(full_text_parts).strip()
        return combined_text, metadata

    @classmethod
    def extract_text_from_docx_bytes(cls, docx_bytes: bytes) -> Tuple[str, Dict[str, Any]]:
        """
        Extracts paragraphs, table rows, and any embedded scanned images from a DOCX Word document.
        """
        paragraphs: List[str] = []
        metadata = {"pageCount": 1, "ocrEngine": "python_docx"}

        # 1. Extract digital text from paragraphs and tables
        try:
            import docx
            doc = docx.Document(io.BytesIO(docx_bytes))
            for p in doc.paragraphs:
                p_text = p.text.strip()
                if p_text:
                    paragraphs.append(p_text)

            for table in doc.tables:
                for row in table.rows:
                    row_cells = [cell.text.strip() for cell in row.cells if cell.text.strip()]
                    if row_cells:
                        paragraphs.append(" | ".join(row_cells))
        except Exception as exc:
            logger.warning(f"python-docx extraction failed, trying zipfile XML parser: {exc}")
            import zipfile
            import xml.etree.ElementTree as ET
            try:
                with zipfile.ZipFile(io.BytesIO(docx_bytes)) as z:
                    xml_content = z.read("word/document.xml")
                tree = ET.fromstring(xml_content)
                ns = {"w": "http://schemas.openxmlformats.org/wordprocessingml/2006/main"}
                for p in tree.iterfind(".//w:p", ns):
                    texts = [node.text for node in p.iterfind(".//w:t", ns) if node.text]
                    if texts:
                        paragraphs.append("".join(texts).strip())
            except Exception as e:
                logger.error(f"DOCX XML extraction also failed: {e}")

        # 2. Extract and OCR any embedded images in word/media/
        try:
            import zipfile
            with zipfile.ZipFile(io.BytesIO(docx_bytes)) as z:
                media_files = [
                    name for name in z.namelist()
                    if name.startswith("word/media/") and any(
                        name.lower().endswith(ext)
                        for ext in [".png", ".jpg", ".jpeg", ".webp", ".bmp", ".tiff", ".gif"]
                    )
                ]
                for img_name in media_files:
                    img_bytes = z.read(img_name)
                    if len(img_bytes) > 2048:  # ignore tiny icons / bullets
                        logger.info(f"Found embedded image {img_name} ({len(img_bytes)} bytes) in DOCX. Running OCR...")
                        try:
                            img_text, _ = cls.extract_text_from_image_bytes(img_bytes)
                            if img_text.strip():
                                paragraphs.append(f"--- Document Content ({img_name}) ---\n{img_text.strip()}")
                        except Exception as ocr_err:
                            logger.warning(f"OCR failed for embedded image {img_name}: {ocr_err}")
        except Exception as media_err:
            logger.warning(f"Could not inspect embedded media in DOCX: {media_err}")

        text = "\n".join(paragraphs).strip()
        return text, metadata
