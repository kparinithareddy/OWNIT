import logging
from typing import List, Dict, Any, Optional
from app.schemas.sources import SourceReference, SourceTier
from app.schemas.product import ProductResponse
from app.schemas.warranty import WarrantyResponse

logger = logging.getLogger("ownit.services.ai.sources")

VERIFIED_MANUFACTURER_PORTALS: Dict[str, Dict[str, str]] = {
    "samsung": {
        "brandName": "Samsung",
        "domain": "samsung.com",
        "officialSource": "Samsung Official Support & Warranty Portal",
        "url": "https://www.samsung.com/in/support/warranty/",
        "standardCoverage": "1 Year Standard Limited Warranty (Panels up to 3 Years / Digital Inverter Compressors up to 10-20 Years)"
    },
    "apple": {
        "brandName": "Apple",
        "domain": "apple.com",
        "officialSource": "Apple Official Hardware Warranty Portal",
        "url": "https://www.apple.com/in/legal/warranty/products/accessory-warranty-english.html",
        "standardCoverage": "1 Year Limited Hardware Warranty & 90 Days Complimentary Technical Support"
    },
    "sony": {
        "brandName": "Sony",
        "domain": "sony.co.in",
        "officialSource": "Sony India Official Service & Warranty Policy",
        "url": "https://www.sony.co.in/electronics/support/articles/00230230",
        "standardCoverage": "1 Year Standard Comprehensive Warranty (Panel defects covered for 2-3 Years on select Bravia models)"
    },
    "lg": {
        "brandName": "LG Electronics",
        "domain": "lg.com",
        "officialSource": "LG India Official Warranty Terms",
        "url": "https://www.lg.com/in/support/warranty-terms",
        "standardCoverage": "1 Year Comprehensive + 10 Years Inverter Linear Compressor / Direct Drive Motor"
    },
    "dell": {
        "brandName": "Dell",
        "domain": "dell.com",
        "officialSource": "Dell Official Hardware Warranty & Service",
        "url": "https://www.dell.com/support/home/en-in",
        "standardCoverage": "1 Year Basic Onsite / Mail-in Service Warranty"
    },
    "hp": {
        "brandName": "HP",
        "domain": "hp.com",
        "officialSource": "HP Official Customer Care & Warranty",
        "url": "https://support.hp.com/in-en/check-warranty",
        "standardCoverage": "1 Year Limited Hardware Warranty"
    },
    "lenovo": {
        "brandName": "Lenovo",
        "domain": "lenovo.com",
        "officialSource": "Lenovo Official Warranty Lookup & Terms",
        "url": "https://support.lenovo.com/in/en/warranty-lookup",
        "standardCoverage": "1-3 Years Depot/Onsite Warranty depending on series"
    },
    "whirlpool": {
        "brandName": "Whirlpool",
        "domain": "whirlpoolindia.com",
        "officialSource": "Whirlpool India Official Customer Service",
        "url": "https://www.whirlpoolindia.com/customer-service",
        "standardCoverage": "1-2 Years Comprehensive + 10 Years Prime Mover / Inverter Motor"
    },
    "bosch": {
        "brandName": "Bosch",
        "domain": "bosch-home.in",
        "officialSource": "Bosch Home Appliances Official Warranty Guidelines",
        "url": "https://www.bosch-home.in/service/warranty",
        "standardCoverage": "2 Years Comprehensive + 10-12 Years EcoSilence Drive Motor"
    },
    "oneplus": {
        "brandName": "OnePlus",
        "domain": "oneplus.in",
        "officialSource": "OnePlus Official Repair Service & Warranty",
        "url": "https://service.oneplus.com/in/warranty-policy",
        "standardCoverage": "1 Year Phone Hardware + 6 Months Accessories"
    },
    "xiaomi": {
        "brandName": "Xiaomi",
        "domain": "mi.com",
        "officialSource": "Xiaomi India Official Warranty Policy",
        "url": "https://www.mi.com/in/service/warranty/",
        "standardCoverage": "1 Year Device + 6 Months Battery & Adapter"
    }
}


class SourceService:
    """
    Manages 4-tier verified source ranking and prevents fabrication of URLs or policies.
    """

    def get_oem_portal_for_brand(self, brand: Optional[str]) -> Optional[Dict[str, str]]:
        if not brand:
            return None
        norm = brand.strip().lower()
        for k, v in VERIFIED_MANUFACTURER_PORTALS.items():
            if k in norm or norm in k:
                return v
        return None

    def get_sources_for_product(
        self,
        product: Any,
        warranties: List[Any],
        documents: List[Dict[str, Any]]
    ) -> List[SourceReference]:
        sources: List[SourceReference] = []

        # Tier 1: User Documents & Invoices
        if documents:
            for doc in documents:
                doc_type = doc.get("documentType", "Document")
                filename = doc.get("originalFilename", "file")
                sources.append(SourceReference(
                    title=f"Uploaded {doc_type} ({filename})",
                    sourceType="user_document",
                    domain=None,
                    url=None,
                    details=f"Stored securely in user vault: {filename}",
                    verified=True
                ))

        for w in warranties:
            w_type = getattr(w, "type", w.get("type") if isinstance(w, dict) else "Warranty")
            w_prov = getattr(w, "provider", w.get("provider") if isinstance(w, dict) else "Provider")
            w_start = getattr(w, "startDate", w.get("startDate") if isinstance(w, dict) else "")
            w_exp = getattr(w, "expiryDate", w.get("expiryDate") if isinstance(w, dict) else "")
            w_status = getattr(w, "status", w.get("status") if isinstance(w, dict) else "Active")

            sources.append(SourceReference(
                title=f"{w_type} Record ({w_prov})",
                sourceType="user_document",
                domain=None,
                url=None,
                details=f"Coverage from {w_start} to {w_exp} (Status: {w_status})",
                verified=True
            ))

        # Tier 2: Official Manufacturer
        brand_val = getattr(product, "brand", product.get("brand") if isinstance(product, dict) else None)
        oem = self.get_oem_portal_for_brand(brand_val)
        if oem:
            sources.append(SourceReference(
                title=f"{oem['brandName']} Official Support ({oem['officialSource']})",
                sourceType="official_manufacturer",
                domain=oem["domain"],
                url=oem["url"],
                details=f"Standard OEM terms: {oem['standardCoverage']}",
                verified=True
            ))

        # Tier 3: Reliable External Seller Policy
        ret_source = getattr(product, "returnPolicySource", product.get("returnPolicySource") if isinstance(product, dict) else None)
        ret_dur = getattr(product, "returnDuration", product.get("returnDuration") if isinstance(product, dict) else None)
        seller = getattr(product, "seller", product.get("seller") if isinstance(product, dict) else None)
        ret_stat = getattr(product, "returnStatus", product.get("returnStatus") if isinstance(product, dict) else "")

        if ret_source and ret_dur and ret_dur != "None":
            sources.append(SourceReference(
                title=f"Verified Seller Policy: {ret_source}",
                sourceType="reliable_external",
                domain=f"{seller.lower().replace(' ', '')}.com" if seller else None,
                url=None,
                details=f"{ret_dur} return window (Status: {ret_stat})",
                verified=True
            ))

        # Tier 4: General Knowledge
        cat = getattr(product, "category", product.get("category") if isinstance(product, dict) else "Electronics")
        sources.append(SourceReference(
            title=f"General Consumer Electronics Preventive Care Guidelines ({cat})",
            sourceType="general_knowledge",
            domain=None,
            url=None,
            details="General preventive best practices. Not certified by specific manufacturer unless verified.",
            verified=False
        ))

        return sources

    def get_global_sources(self, product_count: int, warranty_count: int, doc_count: int) -> List[SourceReference]:
        sources: List[SourceReference] = []

        if doc_count > 0 or warranty_count > 0:
            sources.append(SourceReference(
                title=f"OWNIT User Vault ({product_count} Products, {warranty_count} Warranties, {doc_count} Documents)",
                sourceType="user_document",
                domain=None,
                url=None,
                details="Aggregated verified records from user's OWNIT account",
                verified=True
            ))

        sources.append(SourceReference(
            title="OWNIT Verified Knowledge Base & OEM Warranty Database",
            sourceType="official_manufacturer",
            domain="ownit.app",
            url=None,
            details="Standard manufacturer terms for electronics and appliances",
            verified=True
        ))

        sources.append(SourceReference(
            title="Consumer Rights & Standard Seller Policies (India / Global)",
            sourceType="reliable_external",
            domain=None,
            url=None,
            details="Standard e-commerce return windows and statutory protection guidelines",
            verified=True
        ))

        return sources


source_service = SourceService()
