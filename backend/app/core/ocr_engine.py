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

            processed = cls.preprocess_image(image)
            custom_config = r"--oem 3 --psm 6"
            try:
                extracted_text = pytesseract.image_to_string(processed, config=custom_config)
            except Exception:
                extracted_text = pytesseract.image_to_string(processed)

            return extracted_text.strip(), metadata
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
