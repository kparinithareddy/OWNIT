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
from app.schemas.document import DocumentResponse
from app.services.product_service import format_product_doc
from app.services.document_service import format_doc_response

logger = logging.getLogger("ownit.services.ocr")

TEMP_UPLOAD_DIR = os.path.join(os.path.dirname(settings.absolute_upload_dir), "temp")
os.makedirs(TEMP_UPLOAD_DIR, exist_ok=True)

# Known Brands List for entity recognition
KNOWN_BRANDS = [
    "Apple", "Samsung", "Sony", "LG", "Dell", "HP", "Lenovo", "Asus",
    "Acer", "Xiaomi", "OnePlus", "Google", "Bose", "JBL", "Realme",
    "Vivo", "Oppo", "Whirlpool", "Bosch", "IFB", "Haier", "Godrej",
    "Panasonic", "Philips", "Canon", "Nikon", "GoPro", "Nintendo",
    "PlayStation", "Xbox", "Dyson", "Boat", "Noise", "Nothing", "Motorola",
    "Sennheiser", "Marshall", "Voltas", "Daikin", "Carrier", "Blue Star"
]

# Known Retailers List
KNOWN_RETAILERS = [
    "Amazon", "Flipkart", "Reliance Digital", "Croma", "Apple Store",
    "Vijay Sales", "Best Buy", "Walmart", "Samsung SmartCafe", "Poorvika",
    "Sangeetha Mobiles", "Tata CLiQ", "Myntra", "Broma", "Aditya Vision"
]

CATEGORY_KEYWORDS = {
    "Audio": [r"\bheadphones?\b", r"\bearbuds?\b", r"\bsoundbars?\b", r"\bspeakers?\b", r"\bairpods\b", r"\bgalaxy buds\b", r"wh-1000x", r"\bbluetooth speaker\b", r"\bearphones?\b", r"\btws\b"],
    "Mobile": [r"\biphones?\b", r"\bgalaxy\b", r"\bgalaxy\s*[sza]?\d*\b", r"\bpixel\b", r"\bsmartphones?\b", r"\bredmi\b", r"\boneplus\b", r"\bcellular\b", r"\brealme\b", r"\boppo\b", r"\bvivo\b", r"\bmoto\b", r"\bmobile\b", r"\bphones?\b"],
    "Laptop": [r"\bmacbooks?\b", r"\bthinkpads?\b", r"\bxps\b", r"\binspiron\b", r"\bpavilion\b", r"\blegion\b", r"\brog\b", r"\bzenbooks?\b", r"\blaptops?\b", r"\bnotebooks?\b", r"\bideapad\b", r"\bvivobook\b", r"\bsurface\b"],
    "TV": [r"\bbravia\b", r"\boled\b", r"\bqled\b", r"\bsmart tv\b", r"\bled tv\b", r"\btelevision\b", r"\buhd tv\b", r"\bandroid tv\b", r"\b4k tv\b"],
    "Refrigerator": [r"\bfridges?\b", r"\brefrigerators?\b", r"\bdouble door\b", r"\bfrost free\b", r"\bside by side\b", r"\bsingle door\b"],
    "Washing Machine": [r"\bfront load\b", r"\btop load\b", r"\bwashing machine\b", r"\bwasher\b", r"\bdryer\b"],
    "Air Conditioner": [r"\binverter ac\b", r"\bsplit ac\b", r"\bair conditioner\b", r"\bwindow ac\b", r"\b1\.5 ton\b", r"\b2 ton\b"],
    "Camera": [r"\bdslr\b", r"\bmirrorless\b", r"\beos\b", r"\balpha a?\b", r"\blumix\b", r"\baction cam\b", r"\bgopro\b", r"\bcameras?\b", r"\blens\b"],
    "Gaming": [r"\bplaystations?\b", r"\bps[45]\b", r"\bxbox\b", r"\bnintendo\b", r"\bswitch\b", r"\bgamepads?\b", r"\bcontrollers?\b", r"\bconsole\b"],
    "Home Appliance": [r"\bmicrowaves?\b", r"\bvacuum\b", r"\bpurifiers?\b", r"\bmixer grinder\b", r"\birons?\b", r"\bkettles?\b", r"\bovens?\b", r"\btoasters?\b", r"\bblenders?\b"]
}


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
                if candidate.lower() not in ("cashier", "customer", "invoice", "details", "original"):
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
        Supports single item and multi-product line extraction.
        """
        normalized = cls.normalize_text(raw_text)
        seller = default_seller or cls.extract_seller(normalized)
        invoice_no = cls.extract_invoice_number(normalized)
        dates = cls.extract_dates(normalized)
        purchase_date = dates[0] if dates else datetime.now(timezone.utc).strftime("%Y-%m-%d")
        total_amount = cls.extract_total_amount(normalized)
        serial_no, imei = cls.extract_serial_and_imei(normalized)
        warranty_info = cls.extract_warranty_info(normalized)

        # Look for explicit model field in text
        explicit_model_match = re.search(r"(?:Model|Model\s*No|Model\s*#)\s*[:\-]?\s*([A-Za-z0-9\-_]{2,20})", normalized, re.IGNORECASE)
        explicit_model = explicit_model_match.group(1).strip() if explicit_model_match else None

        lines = [line.strip() for line in normalized.split("\n") if line.strip()]
        candidate_items: List[OCRExtractedItem] = []

        # Find lines that contain a brand or product keyword
        item_lines = []
        for line in lines:
            # Skip header / footer lines
            if re.search(r"(tax invoice|subtotal|gstin|cgst|sgst|authorized signatory|thank you|visit again|return policy|grand total|net amount|amount paid|total amount)", line, re.IGNORECASE):
                continue
            
            has_brand = cls.detect_brand(line) is not None
            has_cat = cls.infer_category(line) != "Other"
            
            if has_brand or has_cat:
                item_lines.append(line)

        # If specific item lines were detected, build items from them
        if item_lines:
            for line in item_lines[:5]:  # Limit to 5 items max per receipt scan
                brand = cls.detect_brand(line)
                category = cls.infer_category(line)
                
                # Extract clean name
                clean_name = line
                # Strip leading list indices or field prefixes like "1. ", "Item Description: ", etc.
                clean_name = re.sub(r"^\s*(?:\d+[\.\)]\s*|(?:Item\s*Description|Product\s*Name|Description|Item)\s*[:\-]?\s*)", "", clean_name, flags=re.IGNORECASE)
                
                # Try finding price on that line
                line_price_match = re.search(r"(?:₹|INR|Rs\.?|\$)\s*([\d,]+(?:\.\d{2})?)", line, re.IGNORECASE)
                if not line_price_match:
                    line_price_match = re.search(r"\b([\d,]+\.\d{2})\b", line)

                if line_price_match:
                    item_price = float(line_price_match.group(1).replace(",", ""))
                elif len(item_lines) == 1 and total_amount:
                    item_price = total_amount
                elif total_amount:
                    item_price = round(total_amount / len(item_lines), 2)
                else:
                    item_price = None

                # Clean up name string - strip trailing currency/price and quantity annotations
                clean_name = re.sub(r"(?:[-:]?\s*(?:₹|INR|Rs\.?|\$)\s*[\d,]+(?:\.\d{2})?|\s+[\d,]+\.\d{2})\s*$", "", clean_name, flags=re.IGNORECASE)
                clean_name = re.sub(r"\b(?:qty|quantity|hsn|rate|mrp|discount)\b.*", "", clean_name, flags=re.IGNORECASE).strip()
                if not clean_name:
                    clean_name = f"{brand or 'Product'} ({category})"

                # Model extraction heuristic
                model = explicit_model
                if not model:
                    model_match = re.search(r"\b([A-Za-z0-9]+-[A-Za-z0-9]+|[A-Za-z0-9]{3,8}\d[A-Za-z0-9]{1,4})\b", line)
                    model = model_match.group(1) if model_match else None

                uncertain_fields = []
                confidence = 0.85
                if not item_price:
                    uncertain_fields.append("price")
                    confidence -= 0.15
                if not dates:
                    uncertain_fields.append("purchaseDate")
                    confidence -= 0.1
                if not brand:
                    uncertain_fields.append("brand")
                    confidence -= 0.1

                confidence = max(0.2, min(1.0, confidence))
                conf_level = "high" if confidence >= 0.8 else ("medium" if confidence >= 0.5 else "low")

                candidate_items.append(OCRExtractedItem(
                    name=clean_name[:150],
                    brand=brand,
                    model=model,
                    category=category,
                    purchaseDate=purchase_date,
                    price=item_price,
                    quantity=1,
                    seller=seller,
                    serialNumber=serial_no,
                    imei=imei,
                    warrantyInfo=warranty_info,
                    confidence=round(confidence, 2),
                    confidenceLevel=conf_level,
                    uncertainFields=uncertain_fields
                ))

        # Fallback: if no multi-item lines detected, create single candidate from overall document
        if not candidate_items:
            brand = cls.detect_brand(normalized)
            category = cls.infer_category(normalized)
            fallback_name = f"{brand or 'Purchased Item'} ({category})" if (brand or category != 'Other') else "Receipt Purchase Item"
            
            uncertain_fields = []
            confidence = 0.65
            if not total_amount:
                uncertain_fields.append("price")
                confidence -= 0.2
            if not dates:
                uncertain_fields.append("purchaseDate")
                confidence -= 0.15
            if not brand:
                uncertain_fields.append("brand")
                uncertain_fields.append("name")
                confidence -= 0.15

            confidence = max(0.1, min(1.0, confidence))
            conf_level = "high" if confidence >= 0.8 else ("medium" if confidence >= 0.5 else "low")

            candidate_items.append(OCRExtractedItem(
                name=fallback_name,
                brand=brand,
                model=None,
                category=category,
                purchaseDate=purchase_date,
                price=total_amount,
                quantity=1,
                seller=seller,
                serialNumber=serial_no,
                imei=imei,
                warrantyInfo=warranty_info,
                confidence=round(confidence, 2),
                confidenceLevel=conf_level,
                uncertainFields=uncertain_fields
            ))

        meta = {
            "seller": seller,
            "invoiceNumber": invoice_no,
            "invoiceDate": purchase_date,
            "totalAmount": total_amount,
            "rawText": normalized
        }
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
            if ext_lower == ".pdf":
                raw_text, ocr_meta = OCREngine.extract_text_from_pdf_bytes(file_bytes)
                page_count = ocr_meta.get("pageCount", 1)
            else:
                raw_text, ocr_meta = OCREngine.extract_text_from_image_bytes(file_bytes)
        except Exception as exc:
            logger.error(f"OCR extraction encountered error: {exc}")
            raw_text = ""
            warnings.append("OCR could not cleanly parse this image. Please review and input product details manually.")

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

        # 1. Insert Products
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
            created_products.append(format_product_doc(prod_doc))

        # 2. If tempFileToken is present, move temp receipt file into permanent documents storage
        if payload.tempFileToken and created_products:
            matching_files = [f for f in os.listdir(TEMP_UPLOAD_DIR) if f.startswith(payload.tempFileToken)]
            if matching_files:
                temp_filename = matching_files[0]
                temp_file_path = os.path.join(TEMP_UPLOAD_DIR, temp_filename)
                _, ext = os.path.splitext(temp_filename)

                # Attach document to the first created product
                primary_product = created_products[0]
                primary_product_id = primary_product.id

                unique_token = uuid.uuid4().hex[:12]
                stored_filename = f"{user_id[:8]}_{primary_product_id[:8]}_{unique_token}{ext}"
                permanent_path = os.path.join(settings.absolute_upload_dir, stored_filename)

                try:
                    shutil.move(temp_file_path, permanent_path)
                    file_size = os.path.getsize(permanent_path)
                    mime_type = "application/pdf" if ext == ".pdf" else "image/jpeg"

                    doc_record = {
                        "userId": user_id,
                        "productId": primary_product_id,
                        "documentType": payload.documentType or "Purchase Bill",
                        "originalFilename": f"Receipt_{primary_product.name[:20].replace(' ', '_')}{ext}",
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
        return OCRConfirmResponse(
            createdProducts=created_products,
            attachedDocuments=attached_docs,
            message=f"Successfully created {item_count} product{'s' if item_count > 1 else ''} from receipt."
        )


ocr_service = OCRService()
