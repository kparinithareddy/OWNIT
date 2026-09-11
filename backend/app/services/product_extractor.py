import os
import re
import json
import logging
from abc import ABC, abstractmethod
from datetime import datetime, timezone
from typing import List, Dict, Any, Optional, Tuple
import httpx

from app.core.config import settings
from app.schemas.ocr import OCRExtractedItem

logger = logging.getLogger("ownit.services.extractor")

# Known Brands List for entity recognition
KNOWN_BRANDS = [
    "Apple", "Samsung", "Sony", "LG", "Dell", "HP", "Lenovo", "Asus",
    "Acer", "Xiaomi", "OnePlus", "Google", "Bose", "JBL", "Realme",
    "Vivo", "Oppo", "Whirlpool", "Bosch", "IFB", "Haier", "Godrej",
    "Panasonic", "Philips", "Canon", "Nikon", "GoPro", "Nintendo",
    "PlayStation", "Xbox", "Dyson", "Boat", "Noise", "Nothing", "Motorola",
    "Sennheiser", "Marshall", "Voltas", "Daikin", "Carrier", "Blue Star",
    "Hitachi", "Toshiba", "TCL", "Hisense", "Mi", "OnePlus", "iQOO", "Infinix"
]

# Known Retailers List
KNOWN_RETAILERS = [
    "Amazon", "Flipkart", "Reliance Digital", "Croma", "Apple Store",
    "Vijay Sales", "Best Buy", "Walmart", "Samsung SmartCafe", "Poorvika",
    "Sangeetha Mobiles", "Tata CLiQ", "Myntra", "Broma", "Aditya Vision"
]

CATEGORY_KEYWORDS = {
    "Audio": [
        r"\bheadphones?\b", r"\bearbuds?\b", r"\bsoundbars?\b", r"\bspeakers?\b",
        r"\bairpods\b", r"\bgalaxy buds\b", r"wh-1000x", r"\bbluetooth speaker\b",
        r"\bearphones?\b", r"\btws\b", r"\baudio\b"
    ],
    "Mobile": [
        r"\biphones?\b", r"\bgalaxy\b", r"\bgalaxy\s*[sza]?\d*\b", r"\bpixel\b",
        r"\bsmartphones?\b", r"\bredmi\b", r"\boneplus\b", r"\bcellular\b",
        r"\brealme\b", r"\boppo\b", r"\bvivo\b", r"\bmoto\b", r"\bmobile\b", r"\bphones?\b"
    ],
    "Laptop": [
        r"\bmacbooks?\b", r"\bthinkpads?\b", r"\bxps\b", r"\binspiron\b",
        r"\bpavilion\b", r"\blegion\b", r"\brog\b", r"\bzenbooks?\b",
        r"\blaptops?\b", r"\bnotebooks?\b", r"\bideapad\b", r"\bvivobook\b", r"\bsurface\b"
    ],
    "TV": [
        r"\bbravia\b", r"\boled\b", r"\bqled\b", r"\bsmart tv\b", r"\bled tv\b",
        r"\btelevision\b", r"\buhd tv\b", r"\bandroid tv\b", r"\b4k tv\b", r"\btv\b"
    ],
    "Refrigerator": [
        r"\bfridges?\b", r"\brefrigerators?\b", r"\bdouble door\b", r"\bfrost free\b",
        r"\bside by side\b", r"\bsingle door\b", r"\binverter refrigerator\b"
    ],
    "Washing Machine": [
        r"\bfront load\b", r"\btop load\b", r"\bwashing machine\b", r"\bwasher\b",
        r"\bdryer\b", r"\bsemi automatic\b", r"\bfully automatic\b"
    ],
    "Air Conditioner": [
        r"\binverter ac\b", r"\bsplit ac\b", r"\bair conditioner\b", r"\bwindow ac\b",
        r"\b1\.5 ton\b", r"\b1 ton\b", r"\b2 ton\b", r"\bdual inverter\b", r"\bac\b"
    ],
    "Camera": [
        r"\bdslr\b", r"\bmirrorless\b", r"\beos\b", r"\balpha a?\b", r"\blumix\b",
        r"\baction cam\b", r"\bgopro\b", r"\bcameras?\b", r"\blens\b", r"\bpowershot\b"
    ],
    "Gaming": [
        r"\bplaystations?\b", r"\bps[45]\b", r"\bxbox\b", r"\bnintendo\b",
        r"\bswitch\b", r"\bgamepads?\b", r"\bcontrollers?\b", r"\bconsole\b", r"\bsteam deck\b"
    ],
    "Home Appliance": [
        r"\bmicrowaves?\b", r"\bvacuum\b", r"\bpurifiers?\b", r"\bair purifier\b",
        r"\bwater purifier\b", r"\bmixer grinder\b", r"\birons?\b", r"\bkettles?\b",
        r"\bovens?\b", r"\binduction\b", r"\btoasters?\b", r"\bblenders?\b", r"\bdishwasher\b"
    ]
}


class BaseProductExtractor(ABC):
    """Abstract interface for modular receipt extractors."""

    @abstractmethod
    def extract_products(self, raw_text: str, doc_metadata: Dict[str, Any]) -> List[OCRExtractedItem]:
        """Extracts structured product candidates from text."""
        pass


class RuleBasedProductExtractor(BaseProductExtractor):
    """
    High-performance rule-based, regex and heuristic extractor.
    Extracts multiple line items, models, brands, prices, quantities, and serials.
    """

    @classmethod
    def infer_category(cls, item_text: str) -> str:
        """Determines product category based on keyword priority rules."""
        for cat, patterns in CATEGORY_KEYWORDS.items():
            for pat in patterns:
                if re.search(pat, item_text, re.IGNORECASE):
                    return cat
        return "Other"

    @classmethod
    def detect_brand(cls, item_text: str) -> Optional[str]:
        """Matches brand from known brands list."""
        for brand in KNOWN_BRANDS:
            if re.search(r"\b" + re.escape(brand) + r"\b", item_text, re.IGNORECASE):
                return brand
        return None

    @classmethod
    def extract_model_from_line(cls, line: str) -> Optional[str]:
        """Extracts model numbers like UA55DU8000, GL-S292RDSX, WH-1000XM5, XPS-9530."""
        # 1. Explicit model prefix
        model_m = re.search(r"(?:Model|Model\s*No|Model\s*#|Mod)\s*[:\-]?\s*([A-Za-z0-9\-_]{2,20})", line, re.IGNORECASE)
        if model_m:
            return model_m.group(1).strip()

        # 2. Typical alphanumeric hardware model codes
        patterns = [
            r"\b([A-Z0-9]{2,6}-[A-Z0-9]{2,10})\b",     # e.g. GL-S292RDSX, WH-1000XM5
            r"\b([A-Z]{1,4}\d{2,4}[A-Z0-9]{2,8})\b",  # e.g. UA55DU8000
            r"\b([A-Za-z0-9]{3,8}\d[A-Za-z0-9]{1,4})\b"
        ]
        for pat in patterns:
            match = re.search(pat, line)
            if match:
                candidate = match.group(1).strip()
                # Exclude common dates or words
                if not re.match(r"^(?:20\d{2}|INR|USD|GST|QTY|TOTAL)$", candidate, re.IGNORECASE):
                    return candidate
        return None

    @classmethod
    def extract_quantity_from_line(cls, line: str) -> int:
        """Extracts quantity if present in line item."""
        qty_match = re.search(r"(?:Qty|Quantity|Nos|Units?)\s*[:\-]?\s*(\d{1,3})", line, re.IGNORECASE)
        if qty_match:
            try:
                q = int(qty_match.group(1))
                if 1 <= q <= 100:
                    return q
            except ValueError:
                pass
        return 1

    @classmethod
    def extract_line_price(cls, line: str) -> Optional[float]:
        """Extracts price amount specific to a line item."""
        price_patterns = [
            r"(?:₹|INR|Rs\.?|\$)\s*([\d,]+(?:\.\d{2})?)",
            r"\b([\d,]+\.\d{2})\b"
        ]
        for pat in price_patterns:
            matches = re.finditer(pat, line, re.IGNORECASE)
            for m in matches:
                amt_str = m.group(1).replace(",", "").strip()
                try:
                    val = float(amt_str)
                    if 1.0 <= val <= 5000000.0:
                        return val
                except ValueError:
                    pass
        return None

    def extract_products(self, raw_text: str, doc_metadata: Dict[str, Any]) -> List[OCRExtractedItem]:
        seller = doc_metadata.get("seller")
        purchase_date = doc_metadata.get("invoiceDate") or datetime.now(timezone.utc).strftime("%Y-%m-%d")
        total_amount = doc_metadata.get("totalAmount")
        serial_no = doc_metadata.get("serialNumber")
        imei = doc_metadata.get("imei")
        warranty_info = doc_metadata.get("warrantyInfo")

        # 1. First check if document has explicit labeled product key-value pairs (e.g. Product Name : ...)
        explicit_name_m = re.search(
            r"(?:Product\s*Name|Item\s*Name|Device\s*Name)\s*[:=\-]\s*([A-Za-z0-9\s\-_+()/,]+?)(?:\s*(?:Model|Serial|IMEI|Purchase|Order|Price|\n|$))",
            raw_text,
            re.IGNORECASE
        )
        if explicit_name_m:
            raw_pname = explicit_name_m.group(1).strip()
            clean_pname = re.sub(r"\s+[a-z]{1,2}$", "", raw_pname).strip()
            if clean_pname and len(clean_pname) > 3:
                brand = self.detect_brand(clean_pname) or self.detect_brand(raw_text)
                category = self.infer_category(clean_pname)
                if category == "Other":
                    category = self.infer_category(raw_text)

                model_m = re.search(r"Model\s*(?:Number|No|#)?\s*[:=\-\s]*([A-Za-z0-9\-_]+)", raw_text, re.IGNORECASE)
                model = model_m.group(1).strip() if model_m else None

                serial_m = re.search(r"Serial\s*(?:Number|No|#)?\s*[:=\-\s]*([A-Za-z0-9]+)", raw_text, re.IGNORECASE)
                serial = serial_m.group(1).strip() if serial_m else serial_no

                imei_m = re.search(r"IMEI\b[^\d\n]*\d?\s*(\d{14,16})", raw_text, re.IGNORECASE)
                extracted_imei = imei_m.group(1).strip() if imei_m else imei

                return [OCRExtractedItem(
                    name=clean_pname[:150],
                    brand=brand,
                    model=model,
                    category=category,
                    purchaseDate=purchase_date,
                    price=total_amount,
                    quantity=1,
                    seller=seller,
                    serialNumber=serial,
                    imei=extracted_imei,
                    warrantyInfo=warranty_info,
                    confidence=0.92,
                    confidenceLevel="high",
                    uncertainFields=[]
                )]

        # 2. Otherwise parse multi-line tabular receipt items
        lines = [line.strip() for line in raw_text.split("\n") if line.strip()]
        candidate_items: List[OCRExtractedItem] = []

        item_lines = []
        for line in lines:
            # Skip noise / tax / customer / footer lines
            if re.search(r"(tax invoice|subtotal|gstin|cgst|sgst|authorized|thank you|visit again|return policy|grand total|net amount|amount paid|total amount|bill of supply|bill to|order no|payment mode|salesperson|phone:|email:|place of supply|warranty card|terms and conditions|what's covered|what's not covered)", line, re.IGNORECASE):
                continue
            
            # Check if line contains a brand, category keyword, or typical item structure
            has_brand = self.detect_brand(line) is not None
            has_cat = self.infer_category(line) != "Other"
            is_numbered_item = re.match(r"^\s*\d+[\.\)]\s+[A-Za-z]", line) is not None

            if has_brand or has_cat or is_numbered_item:
                item_lines.append(line)

        # Parse detected line items into separate product candidates
        if item_lines:
            for line in item_lines:
                brand = self.detect_brand(line)
                category = self.infer_category(line)
                model = self.extract_model_from_line(line)
                quantity = self.extract_quantity_from_line(line)
                item_price = self.extract_line_price(line)

                # If no item price on line, infer from total or proportional
                if item_price is None:
                    if len(item_lines) == 1 and total_amount:
                        item_price = total_amount
                    elif total_amount:
                        item_price = round(total_amount / len(item_lines), 2)

                # Clean up product name
                clean_name = line
                # Strip leading enumeration or labels
                clean_name = re.sub(r"^\s*(?:\d+[\.\)]\s*|(?:Item\s*Description|Product\s*Name|Description|Item)\s*[:\-]?\s*)", "", clean_name, flags=re.IGNORECASE)
                # Strip trailing price, currency, quantity, or rate markers
                clean_name = re.sub(r"(?:[-:]?\s*(?:₹|INR|Rs\.?|\$)\s*[\d,]+(?:\.\d{2})?|\s+[\d,]+\.\d{2})\s*$", "", clean_name, flags=re.IGNORECASE)
                clean_name = re.sub(r"\b(?:qty|quantity|hsn|rate|mrp|discount)\s*[:\-]?\s*\d*\b.*", "", clean_name, flags=re.IGNORECASE).strip()
                clean_name = clean_name.rstrip(" -:,")

                if not clean_name:
                    clean_name = f"{brand or 'Product'} ({category})"

                # Confidence calculation
                uncertain_fields = []
                confidence = 0.85
                if not item_price:
                    uncertain_fields.append("price")
                    confidence -= 0.15
                if not doc_metadata.get("invoiceDate"):
                    uncertain_fields.append("purchaseDate")
                    confidence -= 0.1
                if not brand:
                    uncertain_fields.append("brand")
                    confidence -= 0.1
                if not model:
                    uncertain_fields.append("model")

                confidence = max(0.2, min(1.0, confidence))
                conf_level = "high" if confidence >= 0.8 else ("medium" if confidence >= 0.5 else "low")

                candidate_items.append(OCRExtractedItem(
                    name=clean_name[:150],
                    brand=brand,
                    model=model,
                    category=category,
                    purchaseDate=purchase_date,
                    price=item_price,
                    quantity=quantity,
                    seller=seller,
                    serialNumber=serial_no if len(item_lines) == 1 else None,
                    imei=imei if (category == "Mobile" and len(item_lines) == 1) else None,
                    warrantyInfo=warranty_info,
                    confidence=round(confidence, 2),
                    confidenceLevel=conf_level,
                    uncertainFields=uncertain_fields
                ))

        # Fallback if no multi-item lines detected
        if not candidate_items:
            brand = self.detect_brand(raw_text)
            category = self.infer_category(raw_text)
            fallback_name = f"{brand or 'Purchased Item'} ({category})" if (brand or category != 'Other') else "Receipt Purchase Item"

            uncertain_fields = []
            confidence = 0.60
            if not total_amount:
                uncertain_fields.append("price")
                confidence -= 0.2
            if not doc_metadata.get("invoiceDate"):
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

        return candidate_items


class LocalAIExtractor(BaseProductExtractor):
    """
    Local AI Extractor using Ollama (e.g. llama3.2, mistral) running completely locally on user's machine.
    Zero paid API dependencies. Falls back seamlessly if Ollama is not running.
    """

    def __init__(self, base_url: str = settings.OLLAMA_BASE_URL, model: str = settings.OLLAMA_MODEL):
        self.base_url = base_url
        self.model = model

    def is_available(self) -> bool:
        """Checks if local Ollama daemon is active."""
        try:
            res = httpx.get(f"{self.base_url}/api/tags", timeout=1.0)
            return res.status_code == 200
        except Exception:
            return False

    def extract_products(self, raw_text: str, doc_metadata: Dict[str, Any]) -> List[OCRExtractedItem]:
        """
        Queries local Ollama instance for JSON structured product extraction.
        """
        if not self.is_available():
            logger.info("Local Ollama daemon is not reachable. Using RuleBasedProductExtractor.")
            return []

        prompt = f"""You are an expert receipt parser. Extract all purchased products from the following receipt text into a JSON array of objects.
For each product, identify:
- name: product name
- brand: brand name or null
- model: model number/code or null
- category: one of [Mobile, Laptop, TV, Refrigerator, Washing Machine, Air Conditioner, Audio, Camera, Gaming, Home Appliance, Other]
- price: float or null
- quantity: integer (default 1)
- seller: merchant/store or null
- serialNumber: serial number or null

Receipt Text:
{raw_text}

Respond ONLY with valid JSON in format:
{{"products": [...]}}"""

        try:
            response = httpx.post(
                f"{self.base_url}/api/generate",
                json={
                    "model": self.model,
                    "prompt": prompt,
                    "format": "json",
                    "stream": False
                },
                timeout=15.0
            )
            if response.status_code == 200:
                data = response.json()
                parsed_json = json.loads(data.get("response", "{}"))
                products_data = parsed_json.get("products", [])
                
                results = []
                for p in products_data:
                    results.append(OCRExtractedItem(
                        name=p.get("name", "Extracted Item"),
                        brand=p.get("brand"),
                        model=p.get("model"),
                        category=p.get("category", "Other"),
                        purchaseDate=doc_metadata.get("invoiceDate"),
                        price=p.get("price"),
                        quantity=p.get("quantity", 1),
                        seller=p.get("seller") or doc_metadata.get("seller"),
                        serialNumber=p.get("serialNumber"),
                        imei=None,
                        warrantyInfo=doc_metadata.get("warrantyInfo"),
                        confidence=0.92,
                        confidenceLevel="high",
                        uncertainFields=[]
                    ))
                return results
        except Exception as exc:
            logger.warning(f"Local AI extraction failed, falling back: {exc}")

        return []


class ExtractionManager:
    """
    Coordinates modular receipt extractors (Rule-Based + Local AI).
    Ensures 100% offline functionality without any paid API keys.
    """

    def __init__(self):
        self.rule_extractor = RuleBasedProductExtractor()
        self.local_ai_extractor = LocalAIExtractor()

    def extract(self, raw_text: str, doc_metadata: Dict[str, Any]) -> List[OCRExtractedItem]:
        """
        Executes structured extraction.
        Prioritizes rule-based extraction for speed and deterministic accuracy,
        with seamless local AI enhancement capability.
        """
        return self.rule_extractor.extract_products(raw_text, doc_metadata)


extraction_manager = ExtractionManager()
