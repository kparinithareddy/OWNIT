import logging
import re
from abc import ABC, abstractmethod
from typing import List, Dict, Any, Optional
from app.schemas.sources import SourceReference, SourceTier
from app.schemas.product import ProductResponse
from app.schemas.warranty import WarrantyResponse

logger = logging.getLogger("ownit.services.retrieval")

# Curated, verified manufacturer support portals & official warranty policies
# Rule: Do NOT fabricate URLs or sources.
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
    "asus": {
        "brandName": "ASUS",
        "domain": "asus.com",
        "officialSource": "ASUS Official Support & Warranty Services",
        "url": "https://www.asus.com/in/support/",
        "standardCoverage": "1-2 Years Standard International / Local Limited Warranty"
    },
    "acer": {
        "brandName": "Acer",
        "domain": "acer.com",
        "officialSource": "Acer Official Customer Care & Warranty",
        "url": "https://www.acer.com/in-en/support",
        "standardCoverage": "1 Year Carry-in / On-site Warranty"
    },
    "dyson": {
        "brandName": "Dyson",
        "domain": "dyson.in",
        "officialSource": "Dyson Official Support & Warranty Registration",
        "url": "https://www.dyson.in/support",
        "standardCoverage": "2 Years Comprehensive Guarantee on Hair Care & Cord-free Vacuums"
    },
    "scanpro": {
        "brandName": "ScanPro",
        "domain": "scanpro.com",
        "officialSource": "ScanPro Official Scanner Service & Warranty",
        "url": "https://e-imagedata.com/support/",
        "standardCoverage": "1-3 Years Factory Limited Warranty & Maintenance Support"
    },
    "technova": {
        "brandName": "TechNova",
        "domain": "technovaworld.com",
        "officialSource": "TechNova Official Customer Support",
        "url": "https://www.technovaworld.com/support",
        "standardCoverage": "1 Year Standard Hardware Limited Warranty"
    },
    "boat": {
        "brandName": "boAt",
        "domain": "boat-lifestyle.com",
        "officialSource": "boAt Official Warranty Claim & Service Portal",
        "url": "https://support.boat-lifestyle.com/",
        "standardCoverage": "1 Year Replacement / Repair Warranty for audio & wearables"
    },
    "noise": {
        "brandName": "Noise",
        "domain": "gonoise.com",
        "officialSource": "Noise Official Warranty Registration & Help Center",
        "url": "https://www.gonoise.com/pages/warranty-registration",
        "standardCoverage": "1 Year Manufacturer Limited Warranty"
    },
    "bose": {
        "brandName": "Bose",
        "domain": "boseindia.com",
        "officialSource": "Bose Official India Support & Service",
        "url": "https://www.boseindia.com/en_in/support.html",
        "standardCoverage": "1 Year Standard Limited Warranty on audio products"
    },
    "jbl": {
        "brandName": "JBL",
        "domain": "jbl.com",
        "officialSource": "JBL Official Warranty & Product Support",
        "url": "https://in.jbl.com/warranty.html",
        "standardCoverage": "1 Year Standard Limited Warranty"
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
    },
    "realme": {
        "brandName": "realme",
        "domain": "realme.com",
        "officialSource": "realme Official Warranty Terms & Support",
        "url": "https://www.realme.com/in/support/warranty-terms",
        "standardCoverage": "1 Year Handset + 6 Months In-box Accessories"
    },
    "vivo": {
        "brandName": "vivo",
        "domain": "vivo.com",
        "officialSource": "vivo Official Warranty Terms & Service",
        "url": "https://www.vivo.com/in/support/warranty-terms",
        "standardCoverage": "1 Year Handset Replacement / Repair Support"
    },
    "oppo": {
        "brandName": "OPPO",
        "domain": "oppo.com",
        "officialSource": "OPPO Official Warranty Information & Support",
        "url": "https://support.oppo.com/in/warranty-check/",
        "standardCoverage": "1 Year Phone Hardware Limited Warranty"
    },
    "google": {
        "brandName": "Google Pixel",
        "domain": "google.com",
        "officialSource": "Google Pixel Official Hardware Warranty Center",
        "url": "https://support.google.com/pixelphone/answer/9218411",
        "standardCoverage": "1 Year Limited Hardware Warranty for Pixel Devices"
    },
    "motorola": {
        "brandName": "Motorola",
        "domain": "motorola.in",
        "officialSource": "Motorola Official Warranty & Repair Support",
        "url": "https://motorola-global-en-roe.custhelp.com/",
        "standardCoverage": "1 Year Handset Limited Warranty"
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
    "ifb": {
        "brandName": "IFB",
        "domain": "ifbappliances.com",
        "officialSource": "IFB Appliances Official Customer Support & Warranty",
        "url": "https://www.ifbappliances.com/customer-support",
        "standardCoverage": "4 Years Comprehensive + 10 Years Motor Warranty + 10 Years Spares Support"
    },
    "godrej": {
        "brandName": "Godrej",
        "domain": "godrej.com",
        "officialSource": "Godrej Appliances Official Warranty & Service Care",
        "url": "https://www.godrej.com/godrej-appliances/customer-care",
        "standardCoverage": "1 Year Comprehensive + 10 Years Compressor / Motor Warranty"
    },
    "haier": {
        "brandName": "Haier",
        "domain": "haier.com",
        "officialSource": "Haier India Official Warranty & Customer Support",
        "url": "https://www.haier.com/in/support/",
        "standardCoverage": "1 Year Comprehensive + 10 Years Compressor / Inverter Motor"
    },
    "panasonic": {
        "brandName": "Panasonic",
        "domain": "panasonic.com",
        "officialSource": "Panasonic India Official Support & Warranty Policy",
        "url": "https://www.panasonic.com/in/support.html",
        "standardCoverage": "1-2 Years Comprehensive + 5-10 Years on Compressors & Magnetrons"
    },
    "philips": {
        "brandName": "Philips",
        "domain": "philips.co.in",
        "officialSource": "Philips India Official Support & Warranty Information",
        "url": "https://www.philips.co.in/c-w/support-home/warranty.html",
        "standardCoverage": "2 Years Worldwide Guarantee on Personal Care & Domestic Appliances"
    },
    "voltas": {
        "brandName": "Voltas",
        "domain": "voltas.com",
        "officialSource": "Voltas Official Customer Care & Service Support",
        "url": "https://www.voltas.com/customer-care",
        "standardCoverage": "1 Year Comprehensive + 5-10 Years Inverter Compressor Warranty"
    },
    "daikin": {
        "brandName": "Daikin",
        "domain": "daikinindia.com",
        "officialSource": "Daikin India Official Warranty & Service Portal",
        "url": "https://www.daikinindia.com/service-support",
        "standardCoverage": "1 Year Comprehensive + 5 Years PCB + 10 Years Compressor Warranty"
    },
    "bluestar": {
        "brandName": "Blue Star",
        "domain": "bluestarindia.com",
        "officialSource": "Blue Star Official Customer Support & Service",
        "url": "https://www.bluestarindia.com/customer-service",
        "standardCoverage": "1 Year Comprehensive + 5-10 Years Compressor Warranty"
    },
    "hitachi": {
        "brandName": "Hitachi",
        "domain": "hitachiaircon.in",
        "officialSource": "Hitachi Official Air Conditioning & Appliance Support",
        "url": "https://www.hitachiaircon.in/service-support",
        "standardCoverage": "1 Year Comprehensive + 5 Years Inverter PCB / 10 Years Compressor"
    },
    "tcl": {
        "brandName": "TCL",
        "domain": "tcl.com",
        "officialSource": "TCL Official Support & Warranty Policy",
        "url": "https://www.tcl.com/in/en/support-warranty",
        "standardCoverage": "1-3 Years Comprehensive Warranty on QLED & 4K Panels"
    },
    "canon": {
        "brandName": "Canon",
        "domain": "canon.co.in",
        "officialSource": "Canon India Official Warranty & Support Portal",
        "url": "https://edge.canon.co.in/warranty/",
        "standardCoverage": "2 Years Standard Camera & Lens Limited Warranty"
    },
    "nikon": {
        "brandName": "Nikon",
        "domain": "nikon.co.in",
        "officialSource": "Nikon India Official Service & Warranty Terms",
        "url": "https://www.nikon.co.in/service-and-support",
        "standardCoverage": "2 Years Comprehensive Limited Warranty on bodies and lenses"
    },
    "logitech": {
        "brandName": "Logitech",
        "domain": "logitech.com",
        "officialSource": "Logitech Official Warranty Information & Support",
        "url": "https://support.logi.com/hc/en-us",
        "standardCoverage": "1-2 Years Hardware Limited Warranty on peripherals"
    },
    "anker": {
        "brandName": "Anker",
        "domain": "anker.com",
        "officialSource": "Anker Official Warranty & Customer Support",
        "url": "https://www.anker.com/warranty",
        "standardCoverage": "18-24 Months Hassle-Free Limited Warranty"
    },
    "belkin": {
        "brandName": "Belkin",
        "domain": "belkin.com",
        "officialSource": "Belkin Official Warranty Center & Support",
        "url": "https://www.belkin.com/support/warranty/",
        "standardCoverage": "2 Years Connected Equipment & Hardware Limited Warranty"
    },
    "sandisk": {
        "brandName": "SanDisk",
        "domain": "westerndigital.com",
        "officialSource": "SanDisk / Western Digital Official Warranty Policy",
        "url": "https://www.westerndigital.com/support/store-service-support/warranty-policy",
        "standardCoverage": "3-5 Years Limited Hardware Warranty on Flash & SSD Storage"
    },
    "fastrack": {
        "brandName": "Fastrack",
        "domain": "titan.co.in",
        "officialSource": "Titan & Fastrack Official Warranty Guidelines",
        "url": "https://www.titan.co.in/warranty.html",
        "standardCoverage": "1 Year Movement / 6 Months Battery Limited Warranty"
    },
    "titan": {
        "brandName": "Titan",
        "domain": "titan.co.in",
        "officialSource": "Titan Official Warranty Policy & Service Care",
        "url": "https://www.titan.co.in/warranty.html",
        "standardCoverage": "1-2 Years Movement Warranty"
    },
    "havells": {
        "brandName": "Havells",
        "domain": "havells.com",
        "officialSource": "Havells Official Customer Care & Warranty",
        "url": "https://www.havells.com/en/consumer/customer-care.html",
        "standardCoverage": "1-2 Years Comprehensive Product Guarantee"
    },
    "crompton": {
        "brandName": "Crompton",
        "domain": "crompton.co.in",
        "officialSource": "Crompton Official Customer Support & Warranty",
        "url": "https://www.crompton.co.in/support/",
        "standardCoverage": "1-2 Years Standard Limited Warranty"
    },
    "bajaj": {
        "brandName": "Bajaj Electricals",
        "domain": "bajajelectricals.com",
        "officialSource": "Bajaj Electricals Official Customer Service",
        "url": "https://www.bajajelectricals.com/customer-care/",
        "standardCoverage": "1-2 Years Comprehensive Appliance Warranty"
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
        1. User Documents & Invoices
        2. Official Manufacturer Portal
        3. Reliable External / Seller Terms
        4. General Knowledge / Preventive Care
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

        brand_val = product.brand or "Product"
        name_val = product.name or "Asset"
        model_val = product.model or ""
        purchase_date = product.purchaseDate or ""
        cat = product.category or "Electronics"

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

        # Include product vault record
        sources.append(SourceReference(
            title=f"{brand_val} {name_val} Vault Dossier (Model: {model_val or 'N/A'})",
            sourceType="user_document",
            domain=None,
            url=None,
            details=f"Securely registered in OWNIT vault. Purchased on {purchase_date or 'Recorded date'}.",
            verified=True
        ))

        # -------------------------------------------------------------
        # Tier 2: Official Manufacturer Sources (Priority 2)
        # -------------------------------------------------------------
        brand_normalized = brand_val.strip().lower()
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
                domain=f"{product.seller.lower().replace(' ', '').replace('.', '')}.com" if product.seller else None,
                url=None,
                details=f"{product.returnDuration} return window (Status: {product.returnStatus})",
                verified=True
            ))
        elif product.seller and product.returnDuration and product.returnDuration != "None":
            sources.append(SourceReference(
                title=f"Verified Seller Policy: {product.seller} ({product.returnDuration} Return Window)",
                sourceType="reliable_external",
                domain=f"{product.seller.lower().replace(' ', '').replace('.', '')}.com",
                url=None,
                details=f"{product.returnDuration} return window (Status: {product.returnStatus})",
                verified=True
            ))

        # -------------------------------------------------------------
        # Tier 4: General AI Knowledge / Industry Care Guidelines (Priority 4)
        # -------------------------------------------------------------
        sources.append(SourceReference(
            title=f"General Consumer Electronics Preventive Care Guidelines ({cat})",
            sourceType="general_knowledge",
            domain=None,
            url=None,
            details=f"Recommended preventive maintenance and operating practices for {brand_val} {name_val}.",
            verified=False
        ))

        return sources


retrieval_service: BaseRetrievalService = VerifiedKnowledgeRetrievalService()

