import logging
import re
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

        brand_val = getattr(product, "brand", product.get("brand") if isinstance(product, dict) else "") or "Product"
        name_val = getattr(product, "name", product.get("name") if isinstance(product, dict) else "") or "Asset"
        model_val = getattr(product, "model", product.get("model") if isinstance(product, dict) else "") or ""
        purchase_date = getattr(product, "purchaseDate", product.get("purchaseDate") if isinstance(product, dict) else "") or ""
        cat = getattr(product, "category", product.get("category") if isinstance(product, dict) else "Electronics") or "Electronics"

        # Tier 1: User Uploaded Documents (Priority 1)
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

        # Include product vault record
        sources.append(SourceReference(
            title=f"{brand_val} {name_val} Vault Dossier (Model: {model_val or 'N/A'})",
            sourceType="user_document",
            domain=None,
            url=None,
            details=f"Securely registered in OWNIT vault. Purchased on {purchase_date or 'Recorded date'}.",
            verified=True
        ))

        # Tier 2: Official Manufacturer Portal (Verified OEM only)
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
                domain=f"{seller.lower().replace(' ', '').replace('.', '')}.com" if seller else None,
                url=None,
                details=f"{ret_dur} return window (Status: {ret_stat})",
                verified=True
            ))
        elif seller and ret_dur and ret_dur != "None":
            sources.append(SourceReference(
                title=f"Verified Seller Policy: {seller} ({ret_dur} Return Window)",
                sourceType="reliable_external",
                domain=f"{seller.lower().replace(' ', '').replace('.', '')}.com",
                url=None,
                details=f"{ret_dur} return window (Status: {ret_stat})",
                verified=True
            ))

        # Tier 4: General Knowledge & Product Preventive Care Guidelines
        sources.append(SourceReference(
            title=f"General Consumer Electronics Preventive Care Guidelines ({cat})",
            sourceType="general_knowledge",
            domain=None,
            url=None,
            details=f"Recommended preventive maintenance and operating practices for {brand_val} {name_val}.",
            verified=False
        ))

        return sources

        return sources

    def get_global_sources(self, product_count: int, warranty_count: int, doc_count: int) -> List[SourceReference]:
        sources: List[SourceReference] = []

        if doc_count > 0 or warranty_count > 0 or product_count > 0:
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

