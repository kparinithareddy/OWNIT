import os
import re
import uuid
import time
import shutil
import logging
from datetime import datetime, timezone
from typing import List, Dict, Any, Optional, Tuple
from bson import ObjectId
from fastapi import UploadFile

from app.core.config import settings
from app.core.database import db_manager
from app.core.exceptions import AppException, ValidationException, NotFoundException
from app.core.ocr_engine import OCREngine
from app.schemas.ocr import (
    OCRExtractedItem,
    OCRScanResponse,
    OCRConfirmRequest,
    OCRConfirmResponse,
    OCRConfirmItem
)
from app.schemas.product import ProductResponse
from app.schemas.warranty import WarrantyCreate
from app.services.product_service import format_product_doc
from app.services.document_service import format_doc_response, validate_magic_bytes, sanitize_filename
from app.services.warranty_service import warranty_service

logger = logging.getLogger("ownit.services.ocr")

TEMP_UPLOAD_DIR = os.path.join(settings.absolute_upload_dir, "temp")
os.makedirs(TEMP_UPLOAD_DIR, exist_ok=True)

from app.services.product_extractor import extraction_manager, KNOWN_BRANDS, KNOWN_RETAILERS, CATEGORY_KEYWORDS


class ReceiptParser:
    """
    Rule-based and regex heuristic parser to extract structured information from OCR text.
    """

    @staticmethod
    def normalize_text(raw_text: str) -> str:
        """Normalizes line endings and redundant whitespace."""
        text = raw_text.replace("\r\n", "\n").replace("\r", "\n")
        text = re.sub(r"[ \t]+", " ", text)
        return text.strip()

    @staticmethod
    def extract_seller(text: str) -> Optional[str]:
        """Detects seller/store name from known list or regex patterns."""
        # 1. Match known retailers
        for retailer in KNOWN_RETAILERS:
            if re.search(r"\b" + re.escape(retailer) + r"\b", text, re.IGNORECASE):
                return retailer

        # 2. Match Seller: / Sold By: / Store: headers
        seller_patterns = [
            r"(?:Sold\s*By|Seller|Merchant|Store|Retailer|Billed\s*By|Vendor)\s*[:\-]?\s*([A-Za-z0-9\s.,&'\-]{3,40})",
            r"(?:Tax\s*Invoice\s*-\s*)([A-Za-z0-9\s.,&'\-]{3,40})",
        ]
        for pattern in seller_patterns:
            match = re.search(pattern, text, re.IGNORECASE)
            if match:
                candidate = match.group(1).strip()
                candidate = re.sub(r"\s+(?:Purchase\s*Date|Invoice\s*Date|Order\s*Date|Date|GSTIN|Phone|Email|Bill|Order).*", "", candidate, flags=re.IGNORECASE).strip()
                if candidate.lower() not in ("cashier", "customer", "invoice", "details", "original") and len(candidate) > 2:
                    return candidate.split("\n")[0].strip()

        # 3. Fallback: inspect top lines of receipt
        lines = [line.strip() for line in text.split("\n") if line.strip() and not line.startswith("---")]
        if lines:
            first_line = lines[0]
            if len(first_line) > 2 and len(first_line) < 40 and not re.search(r"(tax|invoice|bill|receipt|gst|date)", first_line, re.IGNORECASE):
                return first_line

        return None

    @staticmethod
    def extract_invoice_number(text: str) -> Optional[str]:
        """Detects Invoice or Receipt or Order Number."""
        patterns = [
            r"(?:Invoice\s*(?:Number|No|Num|#)|Order\s*(?:ID|Number|No|#)|Receipt\s*(?:Number|No|Num|#)|Bill\s*(?:Number|No|Num|#)|Inv\s*#)\s*[:\-#]?\s*([A-Za-z0-9\-_/]{3,30})",
            r"(?:Invoice|Receipt|Order|Bill)\s*[:\-#]\s*([A-Za-z0-9\-_/]{3,30})"
        ]
        for pattern in patterns:
            match = re.search(pattern, text, re.IGNORECASE)
            if match:
                val = match.group(1).strip()
                if val.lower() not in ("date", "number", "num", "details", "summary", "tax", "bill", "cashier"):
                    return val
        return None

    @staticmethod
    def extract_dates(text: str) -> List[str]:
        """Finds and standardizes dates from text into YYYY-MM-DD format."""
        found_dates: List[str] = []
        
        # 1. ISO format: YYYY-MM-DD
        iso_matches = re.findall(r"\b(20\d{2}[-/.]\d{1,2}[-/.]\d{1,2})\b", text)
        for m in iso_matches:
            try:
                parts = re.split(r"[-/.]", m)
                dt = datetime(int(parts[0]), int(parts[1]), int(parts[2]))
                found_dates.append(dt.strftime("%Y-%m-%d"))
            except Exception:
                pass

        # 2. Standard format: DD/MM/YYYY or DD-MM-YYYY
        std_matches = re.findall(r"\b(\d{1,2}[-/.]\d{1,2}[-/.](?:20)?\d{2})\b", text)
        for m in std_matches:
            try:
                parts = re.split(r"[-/.]", m)
                d, mth, y = int(parts[0]), int(parts[1]), int(parts[2])
                if y < 100:
                    y += 2000
                if mth <= 12 and d <= 31:
                    dt = datetime(y, mth, d)
                    found_dates.append(dt.strftime("%Y-%m-%d"))
            except Exception:
                pass

        # 3. Word format: 15 Aug 2024 or August 15, 2024
        word_matches = re.findall(r"\b(\d{1,2}\s+(?:Jan|Feb|Mar|Apr|May|Jun|Jul|Aug|Sep|Oct|Nov|Dec)[a-z]*\s+(?:20)?\d{2})\b", text, re.IGNORECASE)
        for m in word_matches:
            for fmt in ("%d %b %Y", "%d %B %Y", "%d %b %y"):
                try:
                    dt = datetime.strptime(m.strip(), fmt)
                    found_dates.append(dt.strftime("%Y-%m-%d"))
                    break
                except Exception:
                    pass

        return list(dict.fromkeys(found_dates))

    @staticmethod
    def extract_total_amount(text: str) -> Optional[float]:
        """Extracts the grand total or net amount from the receipt."""
        total_patterns = [
            r"(?:Grand\s*Total|Total\s*Amount|Net\s*Amount|Total\s*Payable|Amount\s*Paid|Total)\s*[:\-]?\s*[^0-9\r\n]*\s*([\d,]+(?:\.\d{2})?)",
            r"(?:₹|INR|Rs\.?|\$)\s*([\d,]+\.\d{2})\s*(?:Total|Net)?",
        ]
        for pattern in total_patterns:
            matches = re.finditer(pattern, text, re.IGNORECASE)
            for match in matches:
                amt_str = match.group(1).replace(",", "").strip()
                try:
                    val = float(amt_str)
                    if 1.0 <= val <= 5000000.0:
                        return val
                except ValueError:
                    pass
        return None

    @classmethod
    def infer_category(cls, item_text: str) -> str:
        """Infers product category based on keywords and regex patterns."""
        for cat, patterns in CATEGORY_KEYWORDS.items():
            for pat in patterns:
                if re.search(pat, item_text, re.IGNORECASE):
                    return cat
        return "Other"

    @classmethod
    def detect_brand(cls, item_text: str) -> Optional[str]:
        """Identifies brand from known brands list."""
        for brand in KNOWN_BRANDS:
            if re.search(r"\b" + re.escape(brand) + r"\b", item_text, re.IGNORECASE):
                return brand
        return None

    @classmethod
    def extract_serial_and_imei(cls, text: str) -> Tuple[Optional[str], Optional[str]]:
        """Extracts Serial Number and IMEI if present on invoice."""
        serial_number = None
        imei = None

        sn_match = re.search(r"(?:Serial\s*(?:No|Num|Number|#)?|S/N|SN)\s*[:\-]?\s*([A-Za-z0-9]{6,25})", text, re.IGNORECASE)
        if sn_match:
            serial_number = sn_match.group(1).strip()

        imei_match = re.search(r"(?:IMEI\s*(?:1|2|No|#)?)\s*[:\-]?\s*(\d{15})", text, re.IGNORECASE)
        if imei_match:
            imei = imei_match.group(1).strip()

        return serial_number, imei

    @classmethod
    def extract_warranty_info(cls, text: str) -> Optional[str]:
        """Extracts warranty mention if present on receipt."""
        warranty_match = re.search(r"((?:\d+|one|two|three|1|2|3|4|5)\s*(?:year|yr|years|month|months)\s*(?:comprehensive|manufacturer|brand|limited)?\s*warranty)", text, re.IGNORECASE)
        if warranty_match:
            return warranty_match.group(1).strip().title()
        return None

    @classmethod
    def parse_receipt(cls, raw_text: str, default_seller: Optional[str] = None) -> Tuple[List[OCRExtractedItem], Dict[str, Any]]:
        """
        Parses OCR text into structured items and receipt metadata.
        Uses modular extraction_manager supporting multi-item receipts and local AI models.
        """
        normalized = cls.normalize_text(raw_text)
        seller = default_seller or cls.extract_seller(normalized)
        invoice_no = cls.extract_invoice_number(normalized)
        dates = cls.extract_dates(normalized)
        purchase_date = dates[0] if dates else datetime.now(timezone.utc).strftime("%Y-%m-%d")
        total_amount = cls.extract_total_amount(normalized)
        serial_no, imei = cls.extract_serial_and_imei(normalized)
        warranty_info = cls.extract_warranty_info(normalized)

        meta = {
            "seller": seller,
            "invoiceNumber": invoice_no,
            "invoiceDate": purchase_date,
            "totalAmount": total_amount,
            "serialNumber": serial_no,
            "imei": imei,
            "warrantyInfo": warranty_info,
            "rawText": normalized
        }

        # Delegate structured candidate item extraction to modular extraction pipeline
        candidate_items = extraction_manager.extract(normalized, meta)

        return candidate_items, meta


class OCRService:
    """
    Service coordinating receipt OCR scans, candidate generation, and user confirmation.
    """
    @property
    def db(self):
        database = db_manager.get_db()
        if database is None:
            raise AppException(message="Database service is currently offline.", status_code=503)
        return database

    @property
    def products_collection(self):
        return self.db["products"]

    @property
    def documents_collection(self):
        return self.db["documents"]

    async def scan_receipt(self, file: UploadFile, user_id: str) -> OCRScanResponse:
        """
        Accepts uploaded receipt image or PDF, executes OCR, extracts candidates.
        Does NOT persist products; returns structured candidates with raw text.
        """
        start_time = time.time()
        filename = file.filename or "receipt"
        _, ext = os.path.splitext(filename)
        ext_lower = ext.lower()

        if ext_lower not in settings.ALLOWED_EXTENSIONS:
            allowed_str = ", ".join(settings.ALLOWED_EXTENSIONS)
            raise ValidationException(f"File type '{ext}' is not supported for receipt OCR. Allowed: {allowed_str}")

        file_bytes = await file.read()
        file_size = len(file_bytes)

        if file_size == 0:
            raise ValidationException("Uploaded file is empty.")

        if file_size > settings.MAX_UPLOAD_SIZE_BYTES:
            max_mb = settings.MAX_UPLOAD_SIZE_BYTES / (1024 * 1024)
            raise ValidationException(f"File size exceeds limit of {max_mb:.0f} MB.")

        # Deep magic byte check
        if not validate_magic_bytes(file_bytes, ext_lower):
            raise ValidationException(f"File signature does not match claimed extension '{ext}'. Receipt scan rejected.")

        # Save temporary file for auto-attachment upon confirmation
        temp_token = f"temp_{uuid.uuid4().hex[:16]}"
        temp_filename = f"{temp_token}{ext_lower}"
        temp_path = os.path.join(TEMP_UPLOAD_DIR, temp_filename)

        try:
            with open(temp_path, "wb") as f:
                f.write(file_bytes)
        except Exception as exc:
            logger.warning(f"Failed to write temp receipt file: {exc}")

        # Process OCR based on file type
        raw_text = ""
        page_count = 1
        warnings: List[str] = []

        try:
            if ext_lower in [".docx", ".doc"]:
                raw_text, ocr_meta = OCREngine.extract_text_from_docx_bytes(file_bytes)
                page_count = ocr_meta.get("pageCount", 1)
            elif ext_lower == ".pdf":
                raw_text, ocr_meta = OCREngine.extract_text_from_pdf_bytes(file_bytes)
                page_count = ocr_meta.get("pageCount", 1)
            else:
                raw_text, ocr_meta = OCREngine.extract_text_from_image_bytes(file_bytes)
        except Exception as exc:
            logger.error(f"OCR extraction encountered error: {exc}")
            raw_text = ""
            warnings.append("Could not cleanly parse this document. Please review and input product details manually.")

        if not raw_text.strip():
            raw_text = "[No readable text detected from receipt image/PDF. Please verify the image is clear and well-lit.]"
            warnings.append("No clear text detected. The image might be blurry, too dark, or low contrast. You can edit all fields or scan again.")

        # Parse text into structured candidate items
        items, meta = ReceiptParser.parse_receipt(raw_text)

        # Calculate overall confidence
        if items:
            avg_conf = sum(it.confidence for it in items) / len(items)
        else:
            avg_conf = 0.3
        
        overall_conf = round(avg_conf, 2)
        overall_level = "high" if overall_conf >= 0.8 else ("medium" if overall_conf >= 0.5 else "low")

        elapsed_ms = int((time.time() - start_time) * 1000)

        return OCRScanResponse(
            seller=meta.get("seller"),
            invoiceNumber=meta.get("invoiceNumber"),
            invoiceDate=meta.get("invoiceDate"),
            totalAmount=meta.get("totalAmount"),
            currency="INR",
            overallConfidence=overall_conf,
            overallConfidenceLevel=overall_level,
            items=items,
            rawText=raw_text,
            pageCount=page_count,
            processingTimeMs=elapsed_ms,
            warnings=warnings,
            tempFileToken=temp_token,
            originalFilename=filename,
            fileSize=file_size,
            mimeType=file.content_type or "application/octet-stream"
        )

    async def confirm_and_save(self, user_id: str, payload: OCRConfirmRequest) -> OCRConfirmResponse:
        """
        Persists confirmed candidate items as Products in MongoDB.
        Optionally links the scanned receipt file as a Document to the created products.
        """
        if not payload.items:
            raise ValidationException("At least one item must be confirmed for saving.")

        created_products: List[ProductResponse] = []
        attached_docs: List[DocumentResponse] = []
        now = datetime.now(timezone.utc)

        # 1. Insert Products and Auto-Register Warranties if detected
        registered_warranties_count = 0
        for item in payload.items:
            prod_doc = {
                "userId": user_id,
                "name": item.name.strip(),
                "brand": item.brand.strip() if item.brand else None,
                "model": item.model.strip() if item.model else None,
                "category": item.category,
                "purchaseDate": item.purchaseDate,
                "price": item.price,
                "quantity": item.quantity,
                "seller": item.seller.strip() if item.seller else None,
                "serialNumber": item.serialNumber.strip() if item.serialNumber else None,
                "imei": item.imei.strip() if item.imei else None,
                "notes": item.notes.strip() if item.notes else None,
                "createdAt": now,
                "updatedAt": now
            }
            res = await self.products_collection.insert_one(prod_doc)
            prod_doc["_id"] = res.inserted_id
            created_prod = format_product_doc(prod_doc)
            created_products.append(created_prod)

            # Auto-register warranty component if warranty info was scanned or provided
            if item.warrantyDuration or item.warrantyType or item.warrantyInfo or item.warrantyExpiryDate:
                try:
                    w_create = WarrantyCreate(
                        productId=created_prod.id,
                        type=item.warrantyType or "Manufacturer Warranty",
                        provider=item.warrantyProvider or item.brand or item.seller or "Manufacturer",
                        duration=item.warrantyDuration or "1 Year",
                        startDate=item.warrantyStartDate or item.purchaseDate or now.strftime("%Y-%m-%d"),
                        expiryDate=item.warrantyExpiryDate,
                        benefits=item.warrantyBenefits or "Manufacturing defects and hardware failures under normal use; Complimentary software updates; Authorized service and repair support.",
                        exclusions=item.warrantyExclusions or "Physical or accidental damage (drops, liquid damage); Damage caused by unauthorized repairs or modifications; Software issues due to third-party apps or misuse.",
                        conditions="Valid with original purchase invoice and intact serial/IMEI number.",
                        claimProcedure="Visit any official brand authorized service center or contact customer support.",
                        serviceInformation=item.warrantyServiceInfo or "Official brand authorized customer service center"
                    )
                    await warranty_service.create_warranty(user_id=user_id, data=w_create)
                    registered_warranties_count += 1
                    logger.info(f"Auto-registered warranty component for scanned product {created_prod.id} ({created_prod.name})")
                except Exception as w_exc:
                    logger.warning(f"Could not auto-register warranty for {created_prod.id}: {w_exc}")

        # 2. If tempFileToken is present, move temp receipt file into permanent documents storage
        if payload.tempFileToken and created_products:
            clean_token = payload.tempFileToken.strip()
            # Ensure token contains only safe characters
            if re.match(r"^[a-zA-Z0-9_]{1,64}$", clean_token):
                matching_files = [f for f in os.listdir(TEMP_UPLOAD_DIR) if f.startswith(clean_token)]
                if matching_files:
                    temp_filename = matching_files[0]
                    temp_file_path = os.path.realpath(os.path.join(TEMP_UPLOAD_DIR, temp_filename))
                    temp_dir_canonical = os.path.realpath(TEMP_UPLOAD_DIR)

                    if temp_file_path.startswith(temp_dir_canonical) and os.path.exists(temp_file_path):
                        _, ext = os.path.splitext(temp_filename)

                        # Attach document to the first created product
                        primary_product = created_products[0]
                        primary_product_id = primary_product.id

                        unique_token = uuid.uuid4().hex[:12]
                        stored_filename = f"{user_id[:8]}_{primary_product_id[:8]}_{unique_token}{ext}"
                        permanent_path = os.path.join(settings.absolute_upload_dir, stored_filename)

                        # Ensure target upload directory exists
                        os.makedirs(settings.absolute_upload_dir, exist_ok=True)

                        try:
                            shutil.move(temp_file_path, permanent_path)
                            file_size = os.path.getsize(permanent_path)
                            mime_type = "application/pdf" if ext == ".pdf" else "image/jpeg"

                            clean_product_name = sanitize_filename(primary_product.name[:30])
                            doc_record = {
                                "userId": user_id,
                                "productId": primary_product_id,
                                "documentType": payload.documentType or "Purchase Bill",
                                "originalFilename": f"Receipt_{clean_product_name}{ext}",
                                "storedFilename": stored_filename,
                                "filePath": permanent_path,
                                "mimeType": mime_type,
                                "fileSize": file_size,
                                "uploadedAt": now,
                                "productName": primary_product.name,
                                "productBrand": primary_product.brand
                            }
                            doc_res = await self.documents_collection.insert_one(doc_record)
                            doc_record["_id"] = doc_res.inserted_id
                            attached_docs.append(format_doc_response(doc_record, {"name": primary_product.name, "brand": primary_product.brand}))
                            logger.info(f"Receipt attached as document {doc_record['_id']} to product {primary_product_id}")
                        except Exception as exc:
                            logger.warning(f"Could not finalize temp receipt document attachment: {exc}")

        item_count = len(created_products)
        msg = f"Successfully created {item_count} product{'s' if item_count > 1 else ''}"
        if registered_warranties_count > 0:
            msg += f" and registered {registered_warranties_count} active warranty policy{'s' if registered_warranties_count > 1 else ''}."
        else:
            msg += " from receipt."

        return OCRConfirmResponse(
            createdProducts=created_products,
            attachedDocuments=attached_docs,
            registeredWarrantiesCount=registered_warranties_count,
            message=msg
        )


ocr_service = OCRService()
