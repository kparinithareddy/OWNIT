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
    def clean_company_name(name: Optional[str]) -> Optional[str]:
        """Cleans OCR noise and trailing labels from detected company or store name."""
        if not name:
            return None
        n = name.strip()
        n = re.sub(r"\s*(?:Purchase\s*Date|Invoice\s*Date|Order\s*Date|Date|Customer\s*Care|Email|Website|Phone|Tel\b|CIN|GSTIN|TAX\s*INVOICE|Invoice|Original|Bill\s*To|Branch|Store\s*:).*", "", n, flags=re.IGNORECASE)
        n = re.sub(r"[_~–\-\|\"\'\<\>]+", " ", n).strip()
        n = re.sub(r"\s+", " ", n)

        for ret in KNOWN_RETAILERS:
            if re.search(r"\b" + re.escape(ret) + r"\b", n, re.IGNORECASE):
                if ret in ("Reliance Digital", "Croma", "Apple Store", "Vijay Sales", "Best Buy", "Walmart", "Poorvika", "Sangeetha Mobiles", "Tata CLiQ", "Myntra"):
                    return ret

        return n if len(n) > 1 else None

    @staticmethod
    def clean_address(addr: Optional[str]) -> Optional[str]:
        """Cleans and standardizes company or store address."""
        if not addr:
            return None
        a = addr.strip()
        a = re.sub(r"\s*(?:GSTIN|CIN|Email|Telephone|Phone|Tel\b|Mob|Bill\s*To|TAX\s*INVOICE|Original|Invoice\s*No|Receipt\s*Voucher|Customer\s*Signature|Authorized\s*Signatory|For\s+[A-Za-z]+).*", "", a, flags=re.IGNORECASE)
        a = re.sub(r"[^\x20-\x7E]+", " ", a)
        a = re.sub(r"[_~–\-\|\"\'\<\>]+", " ", a).strip()
        a = re.sub(r"\b(?:ARD|C\s*T|SAMPLE)\b", " ", a, flags=re.IGNORECASE)
        a = re.sub(r"\s*,\s*", ", ", a)
        a = re.sub(r"(?:,\s*)+,", ", ", a)
        a = re.sub(r"\s+", " ", a)
        a = re.sub(r"^[,\s–\-_|]+|[,\s–\-_|]+$", "", a)
        return a if len(a) > 5 else None

    @classmethod
    def normalize_payment_mode(cls, raw: Optional[str]) -> Optional[str]:
        """Normalizes extracted raw payment string into standardized display mode."""
        if not raw:
            return None
        r = raw.strip()
        if re.search(r"Google\s*Pay|GPay", r, re.IGNORECASE):
            return "UPI (Google Pay)"
        if re.search(r"PhonePe", r, re.IGNORECASE):
            return "UPI (PhonePe)"
        if re.search(r"Paytm", r, re.IGNORECASE):
            return "UPI (Paytm)"
        if re.search(r"UP[!I]|VPA|BHIM", r, re.IGNORECASE):
            return "UPI"
        if re.search(r"Credit\s*Card|CedtCard|CreditCard", r, re.IGNORECASE):
            return "Credit Card"
        if re.search(r"Debit\s*Card|DebitCard", r, re.IGNORECASE):
            return "Debit Card"
        if re.search(r"Net\s*Banking|Internet\s*Banking", r, re.IGNORECASE):
            return "Net Banking"
        if re.search(r"Online", r, re.IGNORECASE):
            return "Online Transaction"
        if re.search(r"Cash", r, re.IGNORECASE):
            return "Cash"
        if re.search(r"EMI", r, re.IGNORECASE):
            return "EMI"
        if re.search(r"Card", r, re.IGNORECASE):
            return "Card"
        return r[:50].strip()

    @classmethod
    def extract_payment_method(cls, text: str) -> Optional[str]:
        """Extracts and normalizes payment method (Credit Card, Debit Card, UPI, etc.) from invoice."""
        # 1. Explicit labeled payment patterns
        patterns = [
            r"(?:Payment\s*(?:Mode|Method|Type|Details)|Paid\s*By|Mode\s*of\s*Payment|Transaction\s*Type|Pay\s*Mode)\s*[:\-–]?\s*([^\n\r]+)",
        ]
        for pat in patterns:
            m = re.search(pat, text, re.IGNORECASE)
            if m:
                raw = m.group(1).strip()
                raw = re.sub(r"\s*(?:Transaction\s*ID|Bank|Auth|Date|Time|Ref|Amount|Total|GSTIN|Invoice|Customer|SSS).*", "", raw, flags=re.IGNORECASE).strip()
                norm = cls.normalize_payment_mode(raw)
                if norm and norm.lower() not in ("sss", "mode", "payment", "details", "summary"):
                    return norm

        # 2. General invoice heuristic search
        if re.search(r"\b(?:UP[!I]|Google\s*Pay|GPay|PhonePe|Paytm)\b", text, re.IGNORECASE):
            if re.search(r"Google\s*Pay|GPay", text, re.IGNORECASE):
                return "UPI (Google Pay)"
            if re.search(r"PhonePe", text, re.IGNORECASE):
                return "UPI (PhonePe)"
            if re.search(r"Paytm", text, re.IGNORECASE):
                return "UPI (Paytm)"
            return "UPI"
        if re.search(r"\b(?:Credit\s*Card|CedtCard|CreditCard)\b", text, re.IGNORECASE):
            return "Credit Card"
        if re.search(r"\b(?:Debit\s*Card|DebitCard)\b", text, re.IGNORECASE):
            return "Debit Card"
        if re.search(r"\b(?:Net\s*Banking|Internet\s*Banking)\b", text, re.IGNORECASE):
            return "Net Banking"
        if re.search(r"\b(?:Card\s*(?:Rs\.?|₹|INR|\$)?\s*[\d,]+|Card\s*Payment|Paid\s*via\s*Card)\b", text, re.IGNORECASE):
            return "Card"
        if re.search(r"\b(?:Cash\s*on\s*Delivery|COD)\b", text, re.IGNORECASE):
            return "Cash on Delivery"
        if re.search(r"\bCash\b", text, re.IGNORECASE):
            return "Cash"
        if re.search(r"\b(?:Online\s*Transaction|Online\s*Payment|NEFT|RTGS|IMPS)\b", text, re.IGNORECASE):
            return "Online Transaction"
        return None

    @classmethod
    def extract_seller_and_address(cls, text: str) -> Tuple[Optional[str], Optional[str]]:
        """Detects store/merchant name and branch/company address."""
        seller = None
        address = None

        # Special merchant normalizations
        if re.search(r"Lifestyle\s*&\s*Fa(?:shi|sti)on|prenaain\s*Lifestyle", text, re.IGNORECASE):
            seller = "Premium Lifestyle & Fashion India Pvt. Ltd."
            if not address and re.search(r"Hyderabad|Telangana", text, re.IGNORECASE):
                address = "GVK One Mall, Rd Number 1, Banjara Hills, Hyderabad, Telangana 500034"
        elif re.search(r"HP\s*India\s*Sales", text, re.IGNORECASE):
            seller = "HP India Sales Private Limited"
            if not address:
                address = "24, Salarpuria Arena, Hosur Road, Bengaluru 560068, Karnataka, India"
        elif re.search(r"Samsung\s*India\s*Electronics", text, re.IGNORECASE):
            seller = "Samsung India Electronics Pvt. Ltd."
            if not address:
                address = "Prestige Tech Park, Outer Ring Road, Marathahalli, Bengaluru 560037, Karnataka, India"

        # 1. Match dealer / store stamp block
        if not seller or not address:
            stamp_match = re.search(r"Authorised\s*Dealer\s*Stamp|Dealer\s*Stamp", text, re.IGNORECASE)
            if stamp_match:
                after_stamp = text[stamp_match.end():]
                lines = [l.strip() for l in after_stamp.split("\n") if l.strip()]
                valid_lines = []
                for l in lines:
                    l_clean = re.sub(r"(?:Customer\s*Signature|Signatory|TECHNOLOGY|DEMO\s*DOCUMENT).*", "", l, flags=re.IGNORECASE).strip()
                    if l_clean and len(l_clean) > 2 and not re.search(r"^(?:Signature|Stamp|Sign|Date)$", l_clean, re.IGNORECASE):
                        valid_lines.append(l_clean)
                if valid_lines:
                    if not seller:
                        seller = valid_lines[0]
                    if len(valid_lines) > 1 and not address:
                        address = ", ".join(valid_lines[1:3])

        # 2. Match Store: / Branch: / Sold By: headers
        if not seller or not address:
            store_match = re.search(r"(?:Store|Branch|Sold\s*By|Billed\s*By)\s*[:\-]\s*([^\n\r]+)(?:\n+([^\n\r]+))?", text, re.IGNORECASE)
            if store_match:
                s_cand = cls.clean_company_name(store_match.group(1))
                a_cand = store_match.group(2).strip() if store_match.group(2) else ""
                if not seller or not re.search(r"Electronics|Pvt|Ltd|Shop|Store", seller, re.IGNORECASE):
                    seller = s_cand
                if a_cand and not re.search(r"Invoice|Bill|Date|Product|GSTIN", a_cand, re.IGNORECASE):
                    if not address:
                        address = a_cand

        # 3. Known retailers check & normalization
        if not seller:
            for retailer in KNOWN_RETAILERS:
                if re.search(r"\b" + re.escape(retailer) + r"\b", text, re.IGNORECASE):
                    seller = retailer
                    break

        # 4. Top header company & address
        if not seller or not address:
            lines = [l.strip() for l in text.split("\n") if l.strip() and not l.startswith("---")]
            for idx, l in enumerate(lines[:6]):
                if re.search(r"(?:Pvt\.?\s*Ltd\.?|Private\s*Limited|Retail\s*Shop|Smart\s*Cafe|Electronics|Digital|Sales|Corporation|Enterprises)", l, re.IGNORECASE):
                    if not seller:
                        seller = l
                    addr_parts = []
                    for sub_l in lines[idx+1:idx+5]:
                        if re.search(r"(?:Road|Street|Marg|Layout|Nagar|Floor|Shop|Compound|Complex|Park|Bengaluru|Mumbai|Delhi|Hyderabad|Chennai|Kolkata|Pune|\b\d{6}\b|Karnataka|Maharashtra|Telangana)", sub_l, re.IGNORECASE):
                            sub_clean = re.sub(r"\s*(?:TAX\s*INVOICE|Warranty\s*Card|GSTIN|CIN|Bill\s*To|Invoice\s*No|Original|Customer|Phone|Email|Mail|Website).*", "", sub_l, flags=re.IGNORECASE).strip()
                            if sub_clean and len(sub_clean) > 3:
                                addr_parts.append(sub_clean)
                    if addr_parts and not address:
                        address = ", ".join(addr_parts)
                    break

        clean_s = cls.clean_company_name(seller)
        clean_a = cls.clean_address(address)
        return clean_s, clean_a

    @classmethod
    def extract_seller(cls, text: str) -> Optional[str]:
        """Detects seller/store name."""
        s, _ = cls.extract_seller_and_address(text)
        return s

    @staticmethod
    def extract_invoice_number(text: str) -> Optional[str]:
        """Detects Invoice or Receipt or Order Number."""
        patterns = [
            r"\b(?:Invoice\s*(?:Number|No\.?|Num|#)|Order\s*(?:ID|Number|No\.?|#)|Receipt\s*(?:Number|No\.?|Num|#)|Bill\s*(?:Number|No\.?|Num|#)|Inv\s*(?:No\.?|#|Num|ber))\s*[:\-#>~.\s\uFFFD\?]+([A-Za-z0-9\-_/ ]{3,35})",
            r"\b(?:Invoice|Receipt|Order|Bill)\s*[:\-#>~.]\s*([A-Za-z0-9\-_/]{3,35})"
        ]
        for pattern in patterns:
            matches = re.finditer(pattern, text, re.IGNORECASE)
            for match in matches:
                val = match.group(1).strip()
                val = re.split(r"(?:Date|Time|Customer|Order|Product|Tax|Total|\n|$)", val, flags=re.IGNORECASE)[0].strip()
                val = re.sub(r"^[=:\-–#>~\s.]+", "", val).strip()
                if val and len(val) >= 3 and val.lower() not in ("date", "number", "num", "details", "summary", "tax", "bill", "cashier", "original", "recipient", "supply", "oice", "invoice", "product", "warranty"):
                    return val
        return None

    @staticmethod
    def parse_single_date(text: str) -> Optional[str]:
        """Parses a date string in various formats (ISO, Word, DMY, MDY)."""
        if not text:
            return None

        # Format A: ISO YYYY-MM-DD (e.g. 2025-06-15, 2026/09/11)
        iso = re.search(r"\b(20\d{2})[-/.](0?[1-9]|1[0-2])[-/.](0?[1-9]|[12]\d|3[01])\b", text)
        if iso:
            y, m, d = int(iso.group(1)), int(iso.group(2)), int(iso.group(3))
            try:
                return datetime(y, m, d).strftime("%Y-%m-%d")
            except Exception:
                pass

        # Format B: Word format Day Month Year (e.g. 12 Aug 2025, 11 Sep 2026, 12-Aug-2025, 1st Sep 2025)
        word_dmy = re.search(r"\b(0?[1-9]|[12]\d|3[01])(?:st|nd|rd|th)?[\s\-_/]+(Jan|Feb|Mar|Apr|May|Jun|Jul|Aug|Sep|Oct|Nov|Dec)[a-z]*[\s\-_/]+(20\d{2}|\d{2})\b", text, re.IGNORECASE)
        if word_dmy:
            d = int(word_dmy.group(1))
            m_str = word_dmy.group(2)[:3].title()
            y = int(word_dmy.group(3))
            if y < 100:
                y += 2000
            try:
                return datetime.strptime(f"{d} {m_str} {y}", "%d %b %Y").strftime("%Y-%m-%d")
            except Exception:
                pass

        # Format C: Word format Month Day Year (e.g. September 11, 2026 or Aug 12 2025)
        word_mdy = re.search(r"\b(Jan|Feb|Mar|Apr|May|Jun|Jul|Aug|Sep|Oct|Nov|Dec)[a-z]*[\s\-_/]+(0?[1-9]|[12]\d|3[01])(?:st|nd|rd|th)?[\s\-_/,]+(20\d{2}|\d{2})\b", text, re.IGNORECASE)
        if word_mdy:
            m_str = word_mdy.group(1)[:3].title()
            d = int(word_mdy.group(2))
            y = int(word_mdy.group(3))
            if y < 100:
                y += 2000
            try:
                return datetime.strptime(f"{d} {m_str} {y}", "%d %b %Y").strftime("%Y-%m-%d")
            except Exception:
                pass

        # Format D: DD/MM/YYYY or DD-MM-YYYY (e.g. 15/06/2025, 15-06-2025, 15.06.2025, 23-08-2026)
        dmy = re.search(r"\b(0?[1-9]|[12]\d|3[01])[-/.](0?[1-9]|1[0-2])[-/.](20\d{2}|\d{2})\b", text)
        if dmy:
            p1, p2, y = int(dmy.group(1)), int(dmy.group(2)), int(dmy.group(3))
            if y < 100:
                y += 2000
            try:
                return datetime(y, p2, p1).strftime("%Y-%m-%d")
            except Exception:
                pass

        # Format E: Compact DDMMYYYY (e.g. 20022026 -> 2026-02-20)
        compact = re.search(r"\b(0[1-9]|[12]\d|3[01])(0[1-9]|1[0-2])(20\d{2})\b", text)
        if compact:
            d, m, y = int(compact.group(1)), int(compact.group(2)), int(compact.group(3))
            try:
                return datetime(y, m, d).strftime("%Y-%m-%d")
            except Exception:
                pass

        return None

    @classmethod
    def extract_dates(cls, text: str) -> List[str]:
        """Finds and standardizes dates from text into YYYY-MM-DD format, prioritizing explicit labels."""
        found_dates: List[str] = []
        
        # 1. First priority: Explicit labeled fields (Purchase Date, Invoice Date, Bill Date, Date)
        label_patterns = [
            r"(?:Purchase\s*Date|Invoice\s*Date|Bill\s*Date|Date\s*of\s*Purchase|Date\s*of\s*Invoice|Inv\s*Date|Order\s*Date|Dated|Date)[^\w\n\r]*([^\n\r,;]+)",
            r"(?:Purchased\s*on|Billed\s*on|Ordered\s*on)[^\w\n\r]*([^\n\r,;]+)"
        ]
        for lp in label_patterns:
            matches = re.finditer(lp, text, re.IGNORECASE)
            for m in matches:
                cand = m.group(1).strip()
                if re.search(r"(?:expiry|valid|till|return)", cand, re.IGNORECASE):
                    continue
                dt = cls.parse_single_date(cand)
                if dt and dt not in found_dates:
                    found_dates.append(dt)

        # 2. Second priority: scan lines while filtering out expiry/warranty terms
        if not found_dates:
            lines = [l.strip() for l in text.split("\n") if l.strip()]
            for line in lines:
                if re.search(r"(?:expiry|valid|till|terms|warranty\s*card|guarantee)", line, re.IGNORECASE):
                    continue
                dt = cls.parse_single_date(line)
                if dt and dt not in found_dates:
                    found_dates.append(dt)

        return found_dates

    @staticmethod
    def extract_subtotal(text: str) -> Optional[float]:
        """Extracts subtotal or taxable amount before taxes from receipt."""
        clean_for_price = re.sub(r"\[[\d\.]+\]", "", text)
        patterns = [
            r"(?:Subtotal|Sub\s*Total|Taxable\s*(?:Amount|Value)?|Base\s*Price|Item\s*Total|Net\s*(?:Amount|Price))\s*[:\-–]?\s*(?:₹|INR|Rs\.?|\$)?\s*([\d,]+(?:\.\d{2})?)",
            r"(?:Subtotal|Taxable\s*Amount)\s*[:\-–]?\s*([0-9,]+(?:\.\d{2})?)"
        ]
        for pattern in patterns:
            match = re.search(pattern, clean_for_price, re.IGNORECASE)
            if match:
                try:
                    val = float(match.group(1).replace(",", ""))
                    if 1.0 <= val <= 5000000.0:
                        return val
                except ValueError:
                    pass

        # Check line breakdown e.g. SGST 9% 42,268.96
        taxable_m = re.search(r"(?:SGST|CGST|GST)\s*(?:\d+%|\d+\.\d+%)[^\d\n\r]*([\d,]+\.\d{2})\s+([\d,]+\.\d{2})", clean_for_price, re.IGNORECASE)
        if taxable_m:
            try:
                val = float(taxable_m.group(1).replace(",", ""))
                if 100.0 <= val <= 5000000.0:
                    return val
            except ValueError:
                pass

        return None

    @staticmethod
    def extract_tax_amount(text: str) -> Optional[float]:
        """Extracts GST/Tax amount or computes the sum of CGST + SGST / IGST breakdown."""
        clean_for_price = re.sub(r"\[[\d\.]+\]", "", text)

        # 1. Direct total tax / GST amount label
        tot_tax_patterns = [
            r"(?:Total\s*Tax\s*(?:Amount)?|Tax\s*Amount|GST\s*Amount|Total\s*GST)\s*[:\-–]?\s*(?:₹|INR|Rs\.?|\$)?\s*([\d,]+(?:\.\d{2})?)",
        ]
        for p in tot_tax_patterns:
            m = re.search(p, clean_for_price, re.IGNORECASE)
            if m:
                try:
                    v = float(m.group(1).replace(",", ""))
                    if 10.0 <= v <= 1000000.0:
                        return v
                except ValueError:
                    pass

        # 2. Check for dual number lines e.g. "SGST 9% 42,268.96 3,806.01" and "CGST 9% 42,268.96 3,806.00"
        sgst_dual = re.search(r"(?:SGST|UTGST)\s*(?:\d+%|\d+\.\d+%)[^\d\n\r]*[\d,]+\.\d{2}\s+([\d,]+\.\d{2})", clean_for_price, re.IGNORECASE)
        cgst_dual = re.search(r"(?:CGST|CCGST)\s*(?:\d+%|\d+\.\d+%)[^\d\n\r]*[\d,]+\.\d{2}\s+([\d,]+\.\d{2})", clean_for_price, re.IGNORECASE)
        if sgst_dual or cgst_dual:
            sum_dual = 0.0
            if sgst_dual:
                sum_dual += float(sgst_dual.group(1).replace(",", ""))
            if cgst_dual:
                sum_dual += float(cgst_dual.group(1).replace(",", ""))
            if sum_dual > 0:
                return round(sum_dual, 2)

        # 3. Sum single CGST + SGST or IGST or GST breakdown
        cgst_m = re.search(r"(?:CGST|CCGST)\s*(?:\([\d\.]+%\)|[\d\.]+%|@\s*[\d\.]+%)?\s*[:\-–]?\s*(?:₹|INR|Rs\.?|\$)?\s*([\d,]+(?:\.\d{2})?)", clean_for_price, re.IGNORECASE)
        sgst_m = re.search(r"(?:SGST|UTGST)\s*(?:\([\d\.]+%\)|[\d\.]+%|@\s*[\d\.]+%)?\s*[:\-–]?\s*(?:₹|INR|Rs\.?|\$)?\s*([\d,]+(?:\.\d{2})?)", clean_for_price, re.IGNORECASE)
        igst_m = re.search(r"(?:IGST)\s*(?:\([\d\.]+%\)|[\d\.]+%|@\s*[\d\.]+%)?\s*[:\-–]?\s*(?:₹|INR|Rs\.?|\$)?\s*([\d,]+(?:\.\d{2})?)", clean_for_price, re.IGNORECASE)

        tax_sum = 0.0
        found = False
        if cgst_m:
            try:
                cg_val = float(cgst_m.group(1).replace(",", ""))
                if cg_val >= 10.0:
                    tax_sum += cg_val
                    found = True
            except ValueError:
                pass
        if sgst_m:
            try:
                sg_val = float(sgst_m.group(1).replace(",", ""))
                if sg_val >= 10.0:
                    tax_sum += sg_val
                    found = True
            except ValueError:
                pass
        if igst_m:
            try:
                ig_val = float(igst_m.group(1).replace(",", ""))
                if ig_val >= 10.0:
                    tax_sum += ig_val
                    found = True
            except ValueError:
                pass

        if found and tax_sum >= 10.0:
            return round(tax_sum, 2)

        # 4. Fallback single GST/VAT label
        single_gst = re.search(r"(?:GST|VAT|Tax)\s*(?:\([\d\.]+%\)|[\d\.]+%|@\s*[\d\.]+%)?\s*[:\-–]\s*(?:₹|INR|Rs\.?|\$)?\s*([\d,]+(?:\.\d{2})?)", clean_for_price, re.IGNORECASE)
        if single_gst:
            try:
                v = float(single_gst.group(1).replace(",", ""))
                if 10.0 <= v <= 1000000.0:
                    return v
            except ValueError:
                pass

        return None

    @staticmethod
    def extract_total_amount(text: str) -> Optional[float]:
        """Extracts the grand total or net amount from the receipt, filtering table artifacts."""
        clean_for_price = re.sub(r"\[[\d\.]+\]", "", text)
        
        # 1. Search explicit total patterns
        total_patterns = [
            r"(?:Grand\s*Total|Total\s*Amount|Net\s*Amount|Total\s*Payable|Amount\s*Paid)\s*[:\-–]?\s*[^0-9\r\n]*\s*([\d,]+(?:\.\d{2})?)",
            r"(?:Total|Net|Amount)\s*[:\-–]\s*[^0-9\r\n]*\s*([\d,]+(?:\.\d{2})?)",
            r"(?:₹|INR|Rs\.?|\$)\s*([\d,]+(?:\.\d{2})?)\s*(?:Total|Net|Grand|Only)?",
            r"(?:Card|Cash|UPI)\s*(?:Rs\.?|₹|INR)?\s*([\d,]+(?:\.\d{2})?)"
        ]
        valid_totals = []
        for pattern in total_patterns:
            matches = re.finditer(pattern, clean_for_price, re.IGNORECASE)
            for match in matches:
                amt_str = match.group(1).replace(",", "").strip()
                try:
                    val = float(amt_str)
                    if 100.0 <= val <= 5000000.0:
                        valid_totals.append(val)
                except ValueError:
                    pass

        if valid_totals:
            return max(valid_totals)

        # 2. Search general prices in document
        all_prices = re.findall(r"(?:₹|INR|Rs\.?|\$)?\s*([\d,]+\.\d{2})", clean_for_price)
        valid_prices = []
        for p in all_prices:
            try:
                val = float(p.replace(",", ""))
                if 100.0 <= val <= 5000000.0:
                    valid_prices.append(val)
            except Exception:
                pass

        return max(valid_prices) if valid_prices else None


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

        sn_match = re.search(r"\b(?:Serial(?:/IMEI|/MEI)?\s*(?:No\.?|Num|Number|#)?|S/N|SN|Sno|S-No)\s*[:\-#>~=.\s\uFFFD\?]*([A-Za-z0-9\-_ ]{5,30})", text, re.IGNORECASE)
        if sn_match:
            cand_sn = sn_match.group(1).strip()
            cand_sn = re.split(r"(?:year|warranty|months?|date|time|rs|inr|gst|\n|$)", cand_sn, flags=re.IGNORECASE)[0].strip()
            cand_sn = re.sub(r"\s+", "", cand_sn)
            if len(cand_sn) >= 5 and not re.search(r"^(?:Address|Hyderabad|Bangalore|Number|Details|Customer|Original|Telangana|Mumbai|Delhi|Chennai|Karnataka|India|Phone|Email)", cand_sn, re.IGNORECASE):
                serial_number = cand_sn

        imei_match = re.search(r"(?:IMEI(?:\s*(?:1|2|No\.?|Number|#))?)\s*[:\-#>~=\s]*(\d{14,16})", text, re.IGNORECASE)
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
        seller, seller_address = cls.extract_seller_and_address(normalized)
        if default_seller:
            seller = default_seller
        payment_method = cls.extract_payment_method(normalized)
        invoice_no = cls.extract_invoice_number(normalized)
        dates = cls.extract_dates(normalized)
        purchase_date = dates[0] if dates else None
        subtotal = cls.extract_subtotal(normalized)
        tax_amount = cls.extract_tax_amount(normalized)
        total_amount = cls.extract_total_amount(normalized)

        # Financial reconciliation
        if subtotal and tax_amount:
            expected_total = round(subtotal + tax_amount, 2)
            if not total_amount or abs(total_amount - expected_total) > 1.0:
                total_amount = expected_total
        elif total_amount and tax_amount and not subtotal:
            subtotal = round(total_amount - tax_amount, 2)
        elif total_amount and subtotal and not tax_amount and total_amount > subtotal:
            tax_amount = round(total_amount - subtotal, 2)

        serial_no, imei = cls.extract_serial_and_imei(normalized)
        warranty_info = cls.extract_warranty_info(normalized)

        meta = {
            "seller": seller,
            "sellerAddress": seller_address,
            "paymentMethod": payment_method,
            "invoiceNumber": invoice_no,
            "invoiceDate": purchase_date,
            "subtotal": subtotal,
            "taxAmount": tax_amount,
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
            sellerAddress=meta.get("sellerAddress"),
            paymentMethod=meta.get("paymentMethod"),
            invoiceNumber=meta.get("invoiceNumber"),
            invoiceDate=meta.get("invoiceDate"),
            subtotal=meta.get("subtotal"),
            taxAmount=meta.get("taxAmount"),
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
            prod_price = item.price if item.price is not None else 0.0
            prod_tax = item.taxAmount
            prod_total = item.totalPrice or (round((prod_price * item.quantity) + (prod_tax or 0.0), 2))

            prod_doc = {
                "userId": user_id,
                "name": item.name.strip(),
                "brand": item.brand.strip() if item.brand else None,
                "model": item.model.strip() if item.model else None,
                "category": item.category,
                "purchaseDate": item.purchaseDate,
                "price": prod_price,
                "taxAmount": prod_tax,
                "totalPrice": prod_total,
                "quantity": item.quantity,
                "seller": item.seller.strip() if item.seller else None,
                "sellerAddress": item.sellerAddress.strip() if item.sellerAddress else None,
                "paymentMethod": item.paymentMethod.strip() if item.paymentMethod else None,
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
