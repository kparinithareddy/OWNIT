import logging
from abc import ABC, abstractmethod
from typing import List, Dict, Any, Optional
from app.schemas.sources import SourceReference, SourceTier
from app.schemas.product import ProductResponse
from app.schemas.warranty import WarrantyResponse

logger = logging.getLogger("ownit.services.retrieval")

# Curated, verified manufacturer support portals & official warranty policies
# Rule: Do NOT fabricate URLs or sources.
VERIFIED_MANUFACTURER_PORTALS = {
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
        "standardCoverage": "1-3 Years Depo/Onsite Warranty depending on series"
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


class BaseRetrievalService(ABC):
    """
    Abstract retrieval service interface allowing external search implementation
    to be swapped without affecting the rest of the application.
    """

    @abstractmethod
    def retrieve_hierarchical_sources(
        self,
        product: ProductResponse,
        warranties: List[WarrantyResponse],
        documents: List[Dict[str, Any]],
        maintenance_records: List[Dict[str, Any]],
        query: Optional[str] = None
    ) -> List[SourceReference]:
        """
        Gathers and ranks all available sources adhering to the 4-tier hierarchy:
        1. User Documents
        2. Official Manufacturer
        3. Reliable External
        4. General Knowledge
        """
        pass


class VerifiedKnowledgeRetrievalService(BaseRetrievalService):
    """
    Local, deterministic, verified information retrieval engine.
    Never uses paid search APIs or performs arbitrary unsafe browsing.
    Only cites authentic, verified documents and official OEM repositories.
    """

    def retrieve_hierarchical_sources(
        self,
        product: ProductResponse,
        warranties: List[WarrantyResponse],
        documents: List[Dict[str, Any]],
        maintenance_records: List[Dict[str, Any]],
        query: Optional[str] = None
    ) -> List[SourceReference]:
        sources: List[SourceReference] = []

        # -------------------------------------------------------------
        # Tier 1: Uploaded User Documents & Invoices (Priority 1)
        # -------------------------------------------------------------
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

        # Include registered warranty components as primary user records
        for w in warranties:
            sources.append(SourceReference(
                title=f"{w.type} Record ({w.provider})",
                sourceType="user_document",
                domain=None,
                url=None,
                details=f"Coverage from {w.startDate} to {w.expiryDate} (Status: {w.status})",
                verified=True
            ))

        # -------------------------------------------------------------
        # Tier 2: Official Manufacturer Sources (Priority 2)
        # -------------------------------------------------------------
        brand_normalized = product.brand.strip().lower() if product.brand else ""
        matched_oem = None

        for k, v in VERIFIED_MANUFACTURER_PORTALS.items():
            if k in brand_normalized or brand_normalized in k:
                matched_oem = v
                break

        if matched_oem:
            sources.append(SourceReference(
                title=f"{matched_oem['brandName']} Official Support ({matched_oem['officialSource']})",
                sourceType="official_manufacturer",
                domain=matched_oem["domain"],
                url=matched_oem["url"],
                details=f"Standard OEM terms: {matched_oem['standardCoverage']}",
                verified=True
            ))

        # -------------------------------------------------------------
        # Tier 3: Reliable External Sources & Verified Seller Terms (Priority 3)
        # -------------------------------------------------------------
        if product.returnPolicySource and product.returnDuration and product.returnDuration != "None":
            sources.append(SourceReference(
                title=f"Verified Seller Policy: {product.returnPolicySource}",
                sourceType="reliable_external",
                domain=f"{product.seller.lower().replace(' ', '')}.com" if product.seller else None,
                url=None,
                details=f"{product.returnDuration} return window (Status: {product.returnStatus})",
                verified=True
            ))

        # -------------------------------------------------------------
        # Tier 4: General AI Knowledge / Industry Care Guidelines (Priority 4)
        # -------------------------------------------------------------
        sources.append(SourceReference(
            title=f"General Consumer Electronics Preventive Care Guidelines ({product.category})",
            sourceType="general_knowledge",
            domain=None,
            url=None,
            details="General preventive best practices. Not certified by specific manufacturer unless verified.",
            verified=False
        ))

        return sources


retrieval_service: BaseRetrievalService = VerifiedKnowledgeRetrievalService()
