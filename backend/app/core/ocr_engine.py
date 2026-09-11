import os
import io
import re
import logging
from typing import Tuple, List, Dict, Any, Optional
from PIL import Image, ImageEnhance, ImageFilter, ImageOps
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
    def preprocess_image(cls, image: Image.Image) -> Tuple[Image.Image, Image.Image]:
        """
        Multi-stage preprocessor for receipt images:
        1. Alpha normalization
        2. High-DPI upscaling
        3. Autocontrast & contrast enhancement
        4. Sharpening & adaptive binary thresholding
        """
        try:
            if image.mode in ("RGBA", "LA", "P"):
                background = Image.new("RGB", image.size, (255, 255, 255))
                if image.mode == "RGBA":
                    background.paste(image, mask=image.split()[3])
                else:
                    background.paste(image)
                image = background
            elif image.mode != "RGB":
                image = image.convert("RGB")

            width, height = image.size
            if max(width, height) < 2000:
                scale_factor = max(2.0, 2400.0 / max(width, height, 1))
                new_size = (int(width * scale_factor), int(height * scale_factor))
                image = image.resize(new_size, Image.Resampling.LANCZOS)

            gray = ImageOps.grayscale(image)
            gray = ImageOps.autocontrast(gray, cutoff=1)

            enhancer = ImageEnhance.Contrast(gray)
            enhanced = enhancer.enhance(1.8)
            sharpened = enhanced.filter(ImageFilter.SHARPEN)

            # Binary threshold image
            binary = sharpened.point(lambda p: 255 if p > 145 else 0, mode="1")

            return sharpened, binary
        except Exception as exc:
            logger.warning(f"Image preprocessing error, continuing with original: {exc}")
            return image, image

    @classmethod
    def extract_text_from_image_bytes(cls, image_bytes: bytes) -> Tuple[str, Dict[str, Any]]:
        metadata = {"pageCount": 1, "ocrEngine": "tesseract_multipass"}
        try:
            image = Image.open(io.BytesIO(image_bytes))
            metadata["originalSize"] = list(image.size)
            metadata["originalMode"] = image.mode

            sharpened, binary = cls.preprocess_image(image)

            passes = []

            # Pass 1: Enhanced grayscale with PSM 6 (Single uniform block of text - ideal for receipts)
            try:
                t1 = pytesseract.image_to_string(sharpened, config=r"--oem 3 --psm 6").strip()
                if t1:
                    passes.append(t1)
            except Exception:
                pass

            # Pass 2: Enhanced grayscale with PSM 4 (Single column variable size)
            try:
                t2 = pytesseract.image_to_string(sharpened, config=r"--oem 3 --psm 4").strip()
                if t2:
                    passes.append(t2)
            except Exception:
                pass

            # Pass 3: Binary threshold with PSM 6
            try:
                t3 = pytesseract.image_to_string(binary, config=r"--oem 3 --psm 6").strip()
                if t3:
                    passes.append(t3)
            except Exception:
                pass

            # Pass 4: Auto page segmentation (PSM 3)
            try:
                t4 = pytesseract.image_to_string(sharpened, config=r"--oem 3 --psm 3").strip()
                if t4:
                    passes.append(t4)
            except Exception:
                pass

            if not passes:
                return "", metadata

            # Score each pass by density of key receipt indicators and alphanumeric text
            def score_pass(text: str) -> int:
                score = len(text)
                anchors = ["invoice", "tax", "date", "serial", "model", "brand", "total", "warranty", "amount", "gst", "price", "subtotal", "receipt"]
                for a in anchors:
                    if re.search(r"\b" + a + r"\b", text, re.IGNORECASE):
                        score += 150
                return score

            best_text = max(passes, key=score_pass)
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
