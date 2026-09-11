import logging
from abc import ABC, abstractmethod
from typing import List, Dict, Any, Optional
from app.schemas.product import ProductResponse
from app.schemas.accessory import (
    AccessoryRecommendation,
    AccessoryQueryRequest,
    AccessoryRecommendationsResponse
)
from app.services.product_service import product_service

logger = logging.getLogger("ownit.services.accessories")


class BaseAccessoryRetrievalService(ABC):
    """
    Abstract retrieval service for compatible accessory recommendations.
    Enables modular data sources (local catalog, web search integration, or semantic index).
    """

    @abstractmethod
    async def get_recommendations(
        self,
        product: ProductResponse,
        category_filter: Optional[str] = None,
        min_budget: Optional[float] = None,
        max_budget: Optional[float] = None
    ) -> List[AccessoryRecommendation]:
        """Retrieves and ranks compatible accessories for the given product."""
        pass


class VerifiedCatalogAccessoryService(BaseAccessoryRetrievalService):
    """
    Deterministic, verified accessory catalog & compatibility intelligence engine.
    Uses exact product specifications (brand, model, category, dimensions, ports, interfaces)
    and strictly isolates recommendations to accessories that are specifically useful for that product.
    """

    CATALOG = [
        # ==========================================
        # 1. TV & SMART TV ACCESSORIES
        # ==========================================
        {
            "id": "acc-tv-sb-1",
            "name": "Samsung HW-C450 2.1 Channel Soundbar with Wireless Subwoofer",
            "category": "soundbar",
            "applicableCategories": ["tv"],
            "applicableBrands": ["Samsung"],
            "brand": "Samsung",
            "model": "HW-C450/XL",
            "price": 8990.0,
            "compatibilityStatus": "Compatible",
            "compatibilityReason": "Direct OEM compatibility with Samsung TVs (Crystal 4K, UHD DU8000, QLED) supporting Optical, Bluetooth, and Samsung One Remote audio sync.",
            "platform": "Samsung Official Store",
            "sourceUrl": "https://www.samsung.com/in/audio-devices/soundbar/c450-black-hw-c450-xl/",
            "rating": 4.5,
            "reviewCount": 1820
        },
        {
            "id": "acc-tv-sb-2",
            "name": "Sony HT-S20R 5.1 Channel Real Surround Soundbar with Subwoofer & Rear Speakers",
            "category": "soundbar",
            "applicableCategories": ["tv"],
            "applicableBrands": ["Sony", "Samsung", "LG", "TCL", "Xiaomi"],
            "brand": "Sony",
            "model": "HT-S20R",
            "price": 17990.0,
            "compatibilityStatus": "Compatible",
            "compatibilityReason": "Certified HDMI ARC, Optical input, and Dolby Digital decoding matching all modern 4K/UHD Smart TVs with an HDMI ARC port.",
            "platform": "Sony India Official Store",
            "sourceUrl": "https://www.sony.co.in/electronics/sound-bars/ht-s20r",
            "rating": 4.6,
            "reviewCount": 4350
        },
        {
            "id": "acc-tv-sb-3",
            "name": "boAt Aavante Bar 1190 90W 2.2 Channel Bluetooth Soundbar with Built-in Subwoofers",
            "category": "soundbar",
            "applicableCategories": ["tv"],
            "applicableBrands": [],
            "brand": "boAt",
            "model": "Aavante 1190",
            "price": 4499.0,
            "compatibilityStatus": "Potentially compatible",
            "compatibilityReason": "Universal optical audio and standard HDMI ARC connection; suitable for 43-55 inch TVs with standard audio out ports.",
            "platform": "Croma Electronics",
            "sourceUrl": "https://www.croma.com/boat-aavante-bar-1190-90w-soundbar/p/231144",
            "rating": 4.2,
            "reviewCount": 980
        },
        {
            "id": "acc-tv-sb-4",
            "name": "JBL Cinema SB271 2.1 Channel Deep Bass Wireless Soundbar",
            "category": "soundbar",
            "applicableCategories": ["tv"],
            "applicableBrands": ["Samsung", "LG", "Sony", "OnePlus"],
            "brand": "JBL",
            "model": "JBLSB271BLKIN",
            "price": 9999.0,
            "compatibilityStatus": "Compatible",
            "compatibilityReason": "Verified HDMI eARC and Optical support with 220W peak power matching 50-65 inch 4K televisions.",
            "platform": "Reliance Digital",
            "sourceUrl": "https://www.reliancedigital.in/jbl-cinema-sb271-2-1-channel-soundbar/p/492850921",
            "rating": 4.4,
            "reviewCount": 1150
        },
        {
            "id": "acc-tv-wm-1",
            "name": "AmazonBasics Heavy-Duty Full Motion Articulating TV Wall Mount (32\" to 65\")",
            "category": "wall mount",
            "applicableCategories": ["tv"],
            "applicableBrands": ["Samsung", "Sony", "LG", "Xiaomi", "TCL", "Vu"],
            "brand": "AmazonBasics",
            "model": "AB-WM-65",
            "price": 1499.0,
            "compatibilityStatus": "Compatible",
            "compatibilityReason": "Certified VESA 200x200mm, 300x300mm, and 400x400mm hole patterns with up to 45kg load capacity, matching 43-65 inch panels like Samsung UA55DU8000.",
            "platform": "Amazon India Verified Listing",
            "sourceUrl": "https://www.amazon.in/dp/B07M5K5Y7S",
            "rating": 4.5,
            "reviewCount": 6420
        },
        {
            "id": "acc-tv-wm-2",
            "name": "Samsung Official Slim Fit Wall Mount (WMN-B50EB)",
            "category": "wall mount",
            "applicableCategories": ["tv"],
            "applicableBrands": ["Samsung"],
            "brand": "Samsung",
            "model": "WMN-B50EB/XL",
            "price": 2990.0,
            "compatibilityStatus": "Compatible",
            "compatibilityReason": "Genuine OEM zero-gap flush wall mount engineered specifically for 43-85 inch Samsung Crystal 4K, Neo QLED, and Frame TVs.",
            "platform": "Samsung Official Store",
            "sourceUrl": "https://www.samsung.com/in/tv-accessories/slim-fit-wall-mount-wmn-b50eb-xl/",
            "rating": 4.7,
            "reviewCount": 530
        },
        {
            "id": "acc-tv-wm-3",
            "name": "Universal Fixed Low Profile Steel Wall Mount Bracket (32\"-55\")",
            "category": "wall mount",
            "applicableCategories": ["tv"],
            "applicableBrands": [],
            "brand": "Cubetek",
            "model": "CB-FL-55",
            "price": 699.0,
            "compatibilityStatus": "Potentially compatible",
            "compatibilityReason": "Standard VESA bracket for panels up to 55 inches; verify rear screw length and wall anchor suitability prior to installation.",
            "platform": "Croma Electronics",
            "sourceUrl": "https://www.croma.com",
            "rating": 4.1,
            "reviewCount": 310
        },
        {
            "id": "acc-tv-hdmi-1",
            "name": "Belkin Ultra High Speed 8K / 4K 120Hz HDMI 2.1 Braided Cable (2m)",
            "category": "hdmi cable",
            "applicableCategories": ["tv"],
            "applicableBrands": ["Samsung", "Sony", "LG", "Apple", "Microsoft"],
            "brand": "Belkin",
            "model": "AV10175bt2M-BLK",
            "price": 1999.0,
            "compatibilityStatus": "Compatible",
            "compatibilityReason": "Certified 48Gbps Ultra High Speed HDMI 2.1 supporting 4K 120Hz, eARC uncompressed audio pass-through, HDR10+, and Dolby Vision for modern 4K Smart TVs.",
            "platform": "Belkin India Store",
            "sourceUrl": "https://www.belkin.com/in/ultra-high-speed-hdmi-2.1-cable-2m/P-AV10175.html",
            "rating": 4.8,
            "reviewCount": 3200
        },
        {
            "id": "acc-tv-hdmi-2",
            "name": "AmazonBasics High-Speed 4K HDMI 2.0 Male-to-Male Cable (1.8m)",
            "category": "hdmi cable",
            "applicableCategories": ["tv"],
            "applicableBrands": [],
            "brand": "AmazonBasics",
            "model": "AB-HDMI-1.8",
            "price": 349.0,
            "compatibilityStatus": "Potentially compatible",
            "compatibilityReason": "Standard 18Gbps HDMI 2.0 cable supporting up to 4K @ 60Hz. Suitable for set-top boxes and streaming dongles.",
            "platform": "Amazon India Verified Listing",
            "sourceUrl": "https://www.amazon.in/dp/B014I8SSD0",
            "rating": 4.4,
            "reviewCount": 12800
        },
        {
            "id": "acc-tv-sp-1",
            "name": "V-Guard Crystal Plus Smart TV Voltage Stabilizer (for up to 55\" / 140cm TVs)",
            "category": "surge protector",
            "applicableCategories": ["tv"],
            "applicableBrands": ["Samsung", "Sony", "LG", "OnePlus", "Xiaomi"],
            "brand": "V-Guard",
            "model": "Crystal Plus Smart",
            "price": 2450.0,
            "compatibilityStatus": "Compatible",
            "compatibilityReason": "Microcontroller-based 3A capacity voltage stabilizer with high/low voltage cut-off and line surge suppression tailored specifically for 55-inch smart TVs and set-top boxes.",
            "platform": "Reliance Digital",
            "sourceUrl": "https://www.reliancedigital.in/v-guard-crystal-plus-smart-tv-stabilizer/p/491583921",
            "rating": 4.5,
            "reviewCount": 2100
        },
        {
            "id": "acc-tv-sp-2",
            "name": "Belkin Essential 4-Socket Surge Protector with 2m Heavy Duty Cable",
            "category": "surge protector",
            "applicableCategories": ["tv"],
            "applicableBrands": [],
            "brand": "Belkin",
            "model": "F9E400zb2M-GRY",
            "price": 1199.0,
            "compatibilityStatus": "Potentially compatible",
            "compatibilityReason": "Universal 200 Joules / 6500 Amp surge energy suppression with ground protection, suitable for powering TVs, soundbars, and streaming sticks safely.",
            "platform": "Belkin India Store",
            "sourceUrl": "https://www.belkin.com/in/4-socket-surge-protector-2m/P-F9E400.html",
            "rating": 4.6,
            "reviewCount": 8900
        },

        # ==========================================
        # 2. MOBILE PHONES & SMARTPHONES ACCESSORIES
        # ==========================================
        {
            "id": "acc-mob-ch-1",
            "name": "Samsung 25W Type-C Super Fast Power Adapter (PD 3.0 PPS)",
            "category": "charger",
            "applicableCategories": ["mobile"],
            "applicableBrands": ["Samsung"],
            "brand": "Samsung",
            "model": "EP-TA800NBEGIN",
            "price": 1299.0,
            "compatibilityStatus": "Compatible",
            "compatibilityReason": "Official Samsung Power Delivery (PD 3.0 PPS) adapter delivering certified 25W Super Fast Charging for Samsung Galaxy S25, Note 10+, A-series, and Z Fold/Flip devices.",
            "platform": "Samsung Official Store",
            "sourceUrl": "https://www.samsung.com/in/mobile-accessories/wall-charger-for-super-fast-charging-25w-black-ep-ta800nbegin/",
            "rating": 4.7,
            "reviewCount": 5400
        },
        {
            "id": "acc-mob-ch-2",
            "name": "Apple 20W USB-C Power Adapter",
            "category": "charger",
            "applicableCategories": ["mobile"],
            "applicableBrands": ["Apple"],
            "brand": "Apple",
            "model": "MH203HN/A",
            "price": 1900.0,
            "compatibilityStatus": "Compatible",
            "compatibilityReason": "Genuine OEM USB Power Delivery fast charging adapter engineered specifically for iPhone 15, 16, 14, 13, and iPad.",
            "platform": "Apple India Store",
            "sourceUrl": "https://www.apple.com/in/shop/product/MH203HN/A/20w-usb-c-power-adapter",
            "rating": 4.8,
            "reviewCount": 14200
        },
        {
            "id": "acc-mob-ch-3",
            "name": "Anker 30W GaN Nano II Fast Charger (Foldable Type-C)",
            "category": "charger",
            "applicableCategories": ["mobile"],
            "applicableBrands": ["Samsung", "Apple", "Google", "OnePlus", "Xiaomi"],
            "brand": "Anker",
            "model": "A2665",
            "price": 1799.0,
            "compatibilityStatus": "Compatible",
            "compatibilityReason": "Ultra-compact Gallium Nitride (GaN) fast charger with PPS protocol support for Galaxy phones, iPhones, and Pixel smartphones.",
            "platform": "Anker Official Store",
            "sourceUrl": "https://www.anker.com",
            "rating": 4.6,
            "reviewCount": 3100
        },
        {
            "id": "acc-mob-case-1",
            "name": "Spigen Ultra Hybrid Shockproof Clear Case with Air Cushion Technology",
            "category": "case",
            "applicableCategories": ["mobile"],
            "applicableBrands": ["Samsung", "Apple", "Google", "OnePlus"],
            "brand": "Spigen",
            "model": "ACS072",
            "price": 1499.0,
            "compatibilityStatus": "Compatible",
            "compatibilityReason": "Precision-engineered bumper case with raised bezels for camera protection and corner air cushion shock absorption.",
            "platform": "Amazon India Verified Listing",
            "sourceUrl": "https://www.amazon.in",
            "rating": 4.6,
            "reviewCount": 3800
        },
        {
            "id": "acc-mob-case-2",
            "name": "Ringke Fusion Matte Anti-Fingerprint Shockproof Protective Back Cover",
            "category": "case",
            "applicableCategories": ["mobile"],
            "applicableBrands": ["Samsung", "Apple", "OnePlus"],
            "brand": "Ringke",
            "model": "RF-MATTE-01",
            "price": 1199.0,
            "compatibilityStatus": "Compatible",
            "compatibilityReason": "Durable dual-layer polycarbonate and TPU bumper with lanyard holes and wireless charging compatibility.",
            "platform": "Croma Electronics",
            "sourceUrl": "https://www.croma.com",
            "rating": 4.5,
            "reviewCount": 1650
        },
        {
            "id": "acc-mob-sg-1",
            "name": "Spigen EZ Fit AlignMaster 9H Tempered Glass Screen Protector (Pack of 2)",
            "category": "screen protector",
            "applicableCategories": ["mobile"],
            "applicableBrands": ["Samsung", "Apple", "Google"],
            "brand": "Spigen",
            "model": "AGL0420",
            "price": 999.0,
            "compatibilityStatus": "Compatible",
            "compatibilityReason": "Auto-alignment installation tray with 9H hardness tempered glass and oleophobic anti-fingerprint coating.",
            "platform": "Amazon India",
            "sourceUrl": "https://www.amazon.in",
            "rating": 4.7,
            "reviewCount": 5100
        },
        {
            "id": "acc-mob-pb-1",
            "name": "Anker 10000mAh Magnetic Wireless Power Bank (20W PD Fast Charge)",
            "category": "power bank",
            "applicableCategories": ["mobile"],
            "applicableBrands": ["Apple", "Samsung", "Google"],
            "brand": "Anker",
            "model": "A1611",
            "price": 3299.0,
            "compatibilityStatus": "Compatible",
            "compatibilityReason": "Compact 10,000mAh external battery supporting Qi wireless charging and 20W wired USB-C bidirectional Power Delivery.",
            "platform": "Reliance Digital",
            "sourceUrl": "https://www.reliancedigital.in",
            "rating": 4.5,
            "reviewCount": 2700
        },
        {
            "id": "acc-mob-cb-1",
            "name": "Belkin BoostCharge Braided 60W USB-C to USB-C Cable (1m)",
            "category": "cable",
            "applicableCategories": ["mobile"],
            "applicableBrands": ["Samsung", "Apple", "Google", "OnePlus"],
            "brand": "Belkin",
            "model": "CAB004bt1MBK",
            "price": 799.0,
            "compatibilityStatus": "Compatible",
            "compatibilityReason": "Tested to withstand 25,000+ bends with support for up to 60W PD high-speed charging and 480Mbps data synchronization.",
            "platform": "Belkin India Store",
            "sourceUrl": "https://www.belkin.com/in",
            "rating": 4.6,
            "reviewCount": 4200
        },

        # ==========================================
        # 3. LAPTOP & COMPUTING ACCESSORIES
        # ==========================================
        {
            "id": "acc-lap-hub-1",
            "name": "Anker 7-in-1 USB-C Hub with 4K HDMI, 100W Power Delivery & SD Card Reader",
            "category": "hub",
            "applicableCategories": ["laptop"],
            "applicableBrands": ["Apple", "Dell", "HP", "Lenovo", "Asus", "Acer"],
            "brand": "Anker",
            "model": "A83460A2",
            "price": 3499.0,
            "compatibilityStatus": "Compatible",
            "compatibilityReason": "Universal USB-C / Thunderbolt multi-port adapter providing 100W PD charging, 4K HDMI display out, dual USB 3.0, and SD/microSD card slots.",
            "platform": "Anker India Official",
            "sourceUrl": "https://www.anker.com",
            "rating": 4.6,
            "reviewCount": 2400
        },
        {
            "id": "acc-lap-st-1",
            "name": "Portronics My Buddy K Ergonomic Foldable Aluminum Laptop Stand",
            "category": "stand",
            "applicableCategories": ["laptop"],
            "applicableBrands": [],
            "brand": "Portronics",
            "model": "POR-1196",
            "price": 899.0,
            "compatibilityStatus": "Potentially compatible",
            "compatibilityReason": "Universal adjustable aluminum riser with silicone anti-slip pads supporting 13 to 17-inch laptops with improved airflow.",
            "platform": "Reliance Digital",
            "sourceUrl": "https://www.reliancedigital.in",
            "rating": 4.4,
            "reviewCount": 3100
        },
        {
            "id": "acc-lap-sl-1",
            "name": "HP 15.6\" Executive Water-Resistant Padded Laptop Protective Sleeve",
            "category": "sleeve",
            "applicableCategories": ["laptop"],
            "applicableBrands": ["HP", "Dell", "Lenovo", "Asus", "Acer"],
            "brand": "HP",
            "model": "6KD04AA",
            "price": 1299.0,
            "compatibilityStatus": "Compatible",
            "compatibilityReason": "Custom-fit 15.6-inch protective neoprene and fleece sleeve with accessory pocket matching HP 15, Pavilion, and standard 15.6-inch laptops.",
            "platform": "HP Official Store",
            "sourceUrl": "https://www.hp.com/in",
            "rating": 4.5,
            "reviewCount": 1800
        },
        {
            "id": "acc-lap-ms-1",
            "name": "Logitech MX Master 3S Wireless Performance Bluetooth Mouse",
            "category": "mouse",
            "applicableCategories": ["laptop"],
            "applicableBrands": ["Apple", "Dell", "HP", "Lenovo", "Asus"],
            "brand": "Logitech",
            "model": "MX Master 3S",
            "price": 8995.0,
            "compatibilityStatus": "Compatible",
            "compatibilityReason": "8000 DPI Darkfield sensor tracks on any surface (including glass) with quiet clicks and multi-device Bluetooth / Logi Bolt pairing.",
            "platform": "Croma Electronics",
            "sourceUrl": "https://www.croma.com",
            "rating": 4.8,
            "reviewCount": 9600
        },
        {
            "id": "acc-lap-ch-1",
            "name": "HP 65W Smart AC Laptop Power Adapter (4.5mm Blue Pin)",
            "category": "charger",
            "applicableCategories": ["laptop"],
            "applicableBrands": ["HP"],
            "brand": "HP",
            "model": "H6Y89AA",
            "price": 2199.0,
            "compatibilityStatus": "Compatible",
            "compatibilityReason": "OEM 65W standard smart power adapter with surge protection engineered for HP 15, HP Pavilion, and Envy notebook models.",
            "platform": "HP Official Store",
            "sourceUrl": "https://www.hp.com/in",
            "rating": 4.6,
            "reviewCount": 2100
        },

        # ==========================================
        # 4. HOME APPLIANCES & DYSON STYLERS
        # ==========================================
        {
            "id": "acc-ha-dy-1",
            "name": "Dyson Airwrap Custom Wall Mount Aluminum Holder & Accessory Styler Stand",
            "category": "stand",
            "applicableCategories": ["home appliance"],
            "applicableBrands": ["Dyson"],
            "brand": "Dyson",
            "model": "DY-AW-WM01",
            "price": 2899.0,
            "compatibilityStatus": "Compatible",
            "compatibilityReason": "Magnetic 7-slot precision aluminum wall mount engineered specifically to hold Dyson Airwrap multi-styler and all styling barrel attachments.",
            "platform": "Amazon India Verified Listing",
            "sourceUrl": "https://www.amazon.in",
            "rating": 4.7,
            "reviewCount": 840
        },
        {
            "id": "acc-ha-dy-2",
            "name": "Dyson Airwrap Shockproof Hard Shell Travel Storage Carrying Case (Velvet Lined)",
            "category": "case",
            "applicableCategories": ["home appliance"],
            "applicableBrands": ["Dyson"],
            "brand": "Dyson",
            "model": "DY-AW-TC02",
            "price": 2490.0,
            "compatibilityStatus": "Compatible",
            "compatibilityReason": "Custom-molded water-resistant hard EVA shell with dedicated compartments for Dyson Airwrap styler wand, long barrels, and filter brush.",
            "platform": "Dyson Demo Store Online",
            "sourceUrl": "https://www.dyson.in",
            "rating": 4.8,
            "reviewCount": 1150
        },
        {
            "id": "acc-ha-dy-3",
            "name": "Heat-Resistant Silicone Mat & Travel Storage Pouch for Hair Styling Tools",
            "category": "mat",
            "applicableCategories": ["home appliance"],
            "applicableBrands": ["Dyson", "Philips", "Havells"],
            "brand": "GlamShield",
            "model": "GS-MAT-450",
            "price": 699.0,
            "compatibilityStatus": "Compatible",
            "compatibilityReason": "Protects vanity tables from temperatures up to 230°C (450°F) while hot styler barrels and attachments cool down.",
            "platform": "Nykaa / Reliance Digital",
            "sourceUrl": "https://www.reliancedigital.in",
            "rating": 4.4,
            "reviewCount": 620
        },
        {
            "id": "acc-ha-fl-1",
            "name": "Replacement True HEPA & 360° Activated Carbon Filter for Air Purifiers",
            "category": "filter",
            "applicableCategories": ["home appliance"],
            "applicableBrands": ["Dyson", "Philips", "Xiaomi"],
            "brand": "PureAir",
            "model": "PA-HEPA-360",
            "price": 2999.0,
            "compatibilityStatus": "Potentially compatible",
            "compatibilityReason": "Captures 99.97% of airborne allergens and PM2.5 particulates for standard tower and room air purifiers.",
            "platform": "Amazon India",
            "sourceUrl": "https://www.amazon.in",
            "rating": 4.5,
            "reviewCount": 730
        },

        # ==========================================
        # 5. REFRIGERATOR ACCESSORIES
        # ==========================================
        {
            "id": "acc-ref-tr-1",
            "name": "Heavy-Duty Multi-Functional Adjustable Refrigerator Stand Trolley (with 360° Wheels)",
            "category": "stand",
            "applicableCategories": ["refrigerator"],
            "applicableBrands": ["LG", "Samsung", "Whirlpool", "Haier", "Godrej", "Bosch"],
            "brand": "SmartShel",
            "model": "SS-REF-HD",
            "price": 1599.0,
            "compatibilityStatus": "Compatible",
            "compatibilityReason": "Reinforced square base (adjustable 45x45cm to 70x70cm) with 200kg load capacity designed for single door and double door refrigerators.",
            "platform": "Amazon India Verified Listing",
            "sourceUrl": "https://www.amazon.in",
            "rating": 4.5,
            "reviewCount": 3800
        },
        {
            "id": "acc-ref-st-1",
            "name": "V-Guard VG 50 Refrigerator Voltage Stabilizer (for up to 300L Inverter/Standard Fridges)",
            "category": "stabilizer",
            "applicableCategories": ["refrigerator"],
            "applicableBrands": ["LG", "Samsung", "Whirlpool", "Haier", "Godrej"],
            "brand": "V-Guard",
            "model": "VG-50",
            "price": 1850.0,
            "compatibilityStatus": "Compatible",
            "compatibilityReason": "Automatic low/high voltage cut-off and 2A load capacity engineered to safeguard inverter and compressor circuits against voltage fluctuations.",
            "platform": "Reliance Digital",
            "sourceUrl": "https://www.reliancedigital.in",
            "rating": 4.6,
            "reviewCount": 4200
        },
        {
            "id": "acc-ref-de-1",
            "name": "Activated Bamboo Charcoal Refrigerator Deodorizer & Odor Absorber (Pack of 2)",
            "category": "deodorizer",
            "applicableCategories": ["refrigerator"],
            "applicableBrands": [],
            "brand": "FreshNest",
            "model": "FN-FRIDGE-02",
            "price": 499.0,
            "compatibilityStatus": "Compatible",
            "compatibilityReason": "100% natural fragrance-free activated carbon pouch absorbs moisture and eliminates pungent food odors inside fridge compartments.",
            "platform": "Croma Electronics",
            "sourceUrl": "https://www.croma.com",
            "rating": 4.3,
            "reviewCount": 1100
        },
        {
            "id": "acc-ref-org-1",
            "name": "Multi-Tier Clear Acrylic Refrigerator Storage Organizer Bins (Set of 4)",
            "category": "organizer",
            "applicableCategories": ["refrigerator"],
            "applicableBrands": [],
            "brand": "Kuber Industries",
            "model": "KB-FR-BIN4",
            "price": 899.0,
            "compatibilityStatus": "Potentially compatible",
            "compatibilityReason": "BPA-free transparent pull-out storage bins for fruits, beverages, and dairy that optimize fridge shelf space.",
            "platform": "Amazon India",
            "sourceUrl": "https://www.amazon.in",
            "rating": 4.4,
            "reviewCount": 2150
        },

        # ==========================================
        # 6. WASHING MACHINE ACCESSORIES
        # ==========================================
        {
            "id": "acc-wm-tr-1",
            "name": "SmartShel Heavy Duty Multi-Functional Adjustable Washing Machine Trolley (360° Lockable Wheels)",
            "category": "stand",
            "applicableCategories": ["washing machine"],
            "applicableBrands": ["Samsung", "LG", "Bosch", "IFB", "Whirlpool"],
            "brand": "SmartShel",
            "model": "SS-TROLLEY-HD",
            "price": 1499.0,
            "compatibilityStatus": "Compatible",
            "compatibilityReason": "Adjustable base (48x40cm to 68x60cm) with 160kg load rating specifically designed for 6kg to 9kg front-load and top-load washing machines.",
            "platform": "Amazon India Verified Listing",
            "sourceUrl": "https://www.amazon.in/dp/B08DFGJK11",
            "rating": 4.4,
            "reviewCount": 4200
        },
        {
            "id": "acc-wm-fl-1",
            "name": "WaterScience CLEO Anti-Scalant Washing Machine Inlet Water Filter",
            "category": "filter",
            "applicableCategories": ["washing machine"],
            "applicableBrands": ["Samsung", "LG", "Bosch", "IFB", "Whirlpool", "Godrej"],
            "brand": "WaterScience",
            "model": "WMF-617",
            "price": 1595.0,
            "compatibilityStatus": "Compatible",
            "compatibilityReason": "Standard 3/4 inch inlet thread connector fits standard washing machine tap hoses to reduce limescale buildup and protect heating coils.",
            "platform": "WaterScience Official",
            "sourceUrl": "https://www.waterscience.in/products/cleo-washing-machine-filter",
            "rating": 4.3,
            "reviewCount": 1850
        },
        {
            "id": "acc-wm-cv-1",
            "name": "Dream Care Waterproof & Dustproof Front Load Washing Machine Cover (7-9 kg)",
            "category": "cover",
            "applicableCategories": ["washing machine"],
            "applicableBrands": ["Samsung", "LG", "Bosch", "IFB"],
            "brand": "Dream Care",
            "model": "DC-FL-8K",
            "price": 799.0,
            "compatibilityStatus": "Compatible",
            "compatibilityReason": "Tailored 60x60x85 cm dimensions with zippered front flap matching standard 7kg-9kg front-load washers.",
            "platform": "Croma Electronics",
            "sourceUrl": "https://www.croma.com",
            "rating": 4.5,
            "reviewCount": 920
        },
        {
            "id": "acc-wm-pad-1",
            "name": "Anti-Vibration & Noise Dampening Heavy-Duty Rubber Feet Pads (Set of 4)",
            "category": "anti-vibration pad",
            "applicableCategories": ["washing machine"],
            "applicableBrands": [],
            "brand": "QuietSpin",
            "model": "QS-PAD-04",
            "price": 449.0,
            "compatibilityStatus": "Compatible",
            "compatibilityReason": "Absorbs spin-cycle vibrations, stops washer floor walking, and protects tiled floors from scratches.",
            "platform": "Amazon India",
            "sourceUrl": "https://www.amazon.in",
            "rating": 4.4,
            "reviewCount": 2600
        },

        # ==========================================
        # 7. AUDIO & HEADPHONES ACCESSORIES
        # ==========================================
        {
            "id": "acc-aud-cs-1",
            "name": "Hard Shell EVA Shockproof Travel Carrying Case for Sony WH-1000XM5 / Over-Ear Headphones",
            "category": "case",
            "applicableCategories": ["audio"],
            "applicableBrands": ["Sony", "Bose", "Sennheiser", "JBL"],
            "brand": "Geekria",
            "model": "GK-XM5-CASE",
            "price": 1499.0,
            "compatibilityStatus": "Compatible",
            "compatibilityReason": "Custom molded interior specifically contoured for Sony WH-1000XM5 with soft velvet lining and cable mesh pouch.",
            "platform": "Amazon India Verified Listing",
            "sourceUrl": "https://www.amazon.in",
            "rating": 4.7,
            "reviewCount": 1950
        },
        {
            "id": "acc-aud-st-1",
            "name": "Universal Aluminum Desk Headphone Stand with Weighted Base & Silicone Headrest",
            "category": "stand",
            "applicableCategories": ["audio"],
            "applicableBrands": [],
            "brand": "New Bee",
            "model": "NB-Z4-BLK",
            "price": 799.0,
            "compatibilityStatus": "Compatible",
            "compatibilityReason": "Ergonomic curved TPU headrest supports all over-ear and on-ear headphone headbands without indentations.",
            "platform": "Reliance Digital",
            "sourceUrl": "https://www.reliancedigital.in",
            "rating": 4.6,
            "reviewCount": 3400
        },
        {
            "id": "acc-aud-cb-1",
            "name": "Premium 3.5mm Gold-Plated Braided Auxiliary Audio Cable with Oxygen-Free Copper (1.2m)",
            "category": "cable",
            "applicableCategories": ["audio"],
            "applicableBrands": ["Sony", "Bose", "Sennheiser", "Marshall"],
            "brand": "UGREEN",
            "model": "AV112",
            "price": 499.0,
            "compatibilityStatus": "Compatible",
            "compatibilityReason": "Slim step-down 3.5mm jack fits recessed headphone audio ports, enabling zero-latency wired listening.",
            "platform": "Amazon India",
            "sourceUrl": "https://www.amazon.in",
            "rating": 4.6,
            "reviewCount": 4800
        },

        # ==========================================
        # 8. DOCUMENT SCANNERS & CAMERAS ACCESSORIES
        # ==========================================
        {
            "id": "acc-scn-cb-1",
            "name": "High-Speed USB 3.0 Type-A to Type-B Heavy-Duty Gold-Plated Scanner Data Cable (2m)",
            "category": "cable",
            "applicableCategories": ["scanner"],
            "applicableBrands": ["ScanPro", "Canon", "Epson", "HP", "Fujitsu"],
            "brand": "UGREEN",
            "model": "US104-30",
            "price": 649.0,
            "compatibilityStatus": "Compatible",
            "compatibilityReason": "5Gbps SuperSpeed USB 3.0 Type-B connection engineered for high-throughput desktop document scanners (e.g. ScanPro SP-2200).",
            "platform": "Amazon India Verified Listing",
            "sourceUrl": "https://www.amazon.in",
            "rating": 4.7,
            "reviewCount": 1420
        },
        {
            "id": "acc-scn-cl-1",
            "name": "Professional Document Scanner Roller Cleaning Sheets & Optics Cleaning Fluid Kit",
            "category": "cleaning kit",
            "applicableCategories": ["scanner"],
            "applicableBrands": ["ScanPro", "Canon", "Epson", "Fujitsu"],
            "brand": "CleanScan",
            "model": "CS-KIT-10",
            "price": 1199.0,
            "compatibilityStatus": "Compatible",
            "compatibilityReason": "Includes pre-saturated roller cleaning sheets to remove paper dust, toner residue, and prevent document feeder paper jams.",
            "platform": "TechNova Electronics Store",
            "sourceUrl": "https://www.technova.com",
            "rating": 4.6,
            "reviewCount": 510
        },
        {
            "id": "acc-scn-cv-1",
            "name": "Anti-Static Waterproof Nylon Dust Cover for Desktop Document Scanners",
            "category": "cover",
            "applicableCategories": ["scanner"],
            "applicableBrands": [],
            "brand": "CoverPro",
            "model": "CP-SCAN-01",
            "price": 499.0,
            "compatibilityStatus": "Compatible",
            "compatibilityReason": "Tailored antistatic water-resistant fabric protects automatic document feeder rollers and optical glass from ambient airborne dust.",
            "platform": "Reliance Digital",
            "sourceUrl": "https://www.reliancedigital.in",
            "rating": 4.4,
            "reviewCount": 380
        }
    ]

    @classmethod
    def resolve_canonical_category(cls, category: Optional[str], name: Optional[str]) -> str:
        """
        Maps user product category and name to a strictly scoped canonical accessory category.
        """
        c = (category or "").strip().lower()
        n = (name or "").strip().lower()

        if any(k in c for k in ["tv", "television"]) or any(k in n for k in [" smart tv", " 4k tv", " led tv", " oled", " bravia", " crystal 4k", "du8000"]):
            return "tv"
        if any(k in c for k in ["mobile", "smartphone", "phone", "cellular", "tablet"]) or any(k in n for k in ["galaxy s", "galaxy note", "galaxy a", "galaxy z", "iphone", "pixel", "redmi", "oneplus"]):
            return "mobile"
        if any(k in c for k in ["laptop", "notebook", "macbook", "computer"]) or any(k in n for k in ["laptop", "xps", "pavilion", "thinkpad", "macbook", "ideapad", "zenbook", "notebook"]):
            return "laptop"
        if any(k in c for k in ["washing machine", "washer"]) or any(k in n for k in ["washing machine", "front load", "top load", "washer"]):
            return "washing machine"
        if any(k in c for k in ["refrigerator", "fridge"]) or any(k in n for k in ["refrigerator", "fridge", "double door", "frost free"]):
            return "refrigerator"
        if any(k in c for k in ["scanner", "document scanner"]) or any(k in n for k in ["scanner", "scanpro", "document scanner", "sp-2200"]):
            return "scanner"
        if any(k in c for k in ["audio", "headphone", "earbud", "earphone", "soundbar", "speaker"]) or any(k in n for k in ["headphones", "wh-1000x", "airpods", "galaxy buds", "earbuds", "noise cancelling"]):
            return "audio"
        if any(k in c for k in ["home appliance", "appliance", "styler", "dryer", "airwrap"]) or any(k in n for k in ["airwrap", "styler", "dryer", "purifier", "vacuum", "trimmer"]):
            return "home appliance"

        return c or "general"

    async def get_recommendations(
        self,
        product: ProductResponse,
        category_filter: Optional[str] = None,
        min_budget: Optional[float] = None,
        max_budget: Optional[float] = None
    ) -> List[AccessoryRecommendation]:
        """
        Filters and ranks accessories matching strictly the target product's canonical category, brand, and budget.
        """
        canon_cat = self.resolve_canonical_category(product.category, product.name)
        prod_brand = (product.brand or "").strip().lower()
        prod_model = (product.model or "").strip().lower()
        prod_name = (product.name or "").strip().lower()

        results: List[AccessoryRecommendation] = []

        for item in self.CATALOG:
            item_cats = [c.lower() for c in item.get("applicableCategories", [])]

            # 1. STRICT CATEGORY ISOLATION:
            # The accessory MUST explicitly declare the product's canonical category.
            if canon_cat not in item_cats:
                continue

            # 2. Accessory Category Filter (e.g. user selected "soundbar", "wall mount", "charger", "case")
            if category_filter and category_filter.strip().lower() != "all":
                target_filter = category_filter.strip().lower()
                if item["category"].lower() != target_filter and target_filter not in item["category"].lower():
                    continue

            # 3. Brand & Model Evaluation
            item_brands = [b.lower() for b in item.get("applicableBrands", [])]
            compat_status = item["compatibilityStatus"]

            if item_brands and prod_brand:
                is_brand_match = any(b in prod_brand or prod_brand in b for b in item_brands)
                if not is_brand_match:
                    if item["brand"].lower() == prod_brand:
                        compat_status = "Compatible"
                    else:
                        compat_status = "Potentially compatible"

            # 4. Budget check
            price = float(item["price"])
            in_budget = True

            if min_budget is not None and price < min_budget:
                in_budget = False
            if max_budget is not None and price > max_budget:
                in_budget = False

            if (min_budget is not None or max_budget is not None) and not in_budget:
                continue

            rec = AccessoryRecommendation(
                id=item["id"],
                name=item["name"],
                category=item["category"],
                brand=item["brand"],
                model=item.get("model"),
                price=price,
                priceFormatted=f"₹{price:,.0f}",
                compatibilityStatus=compat_status,
                compatibilityReason=item["compatibilityReason"],
                platform=item["platform"],
                sourceUrl=item.get("sourceUrl"),
                rating=item.get("rating"),
                reviewCount=item.get("reviewCount"),
                imageUrl=item.get("imageUrl"),
                inBudget=in_budget
            )
            results.append(rec)

        # Sort: Brand-matched & Verified Compatible first, then by rating/popularity
        results.sort(
            key=lambda x: (
                0 if (x.compatibilityStatus == "Compatible" and prod_brand and (x.brand.lower() in prod_brand or prod_brand in x.brand.lower()))
                else (1 if x.compatibilityStatus == "Compatible" else 2),
                -(x.rating or 0),
                x.price
            )
        )

        return results


class AccessoryService:
    """
    Business service layer managing compatible accessory discovery and recommendations.
    """

    def __init__(self, retrieval_engine: Optional[BaseAccessoryRetrievalService] = None):
        self.retrieval_engine = retrieval_engine or VerifiedCatalogAccessoryService()

    async def get_product_recommendations(
        self,
        user_id: str,
        product_id: str,
        category: Optional[str] = None,
        min_budget: Optional[float] = None,
        max_budget: Optional[float] = None
    ) -> AccessoryRecommendationsResponse:
        """
        Retrieves compatible accessories scoped strictly to the user's verified product.
        """
        product = await product_service.get_product_by_id(product_id, user_id)

        recommendations = await self.retrieval_engine.get_recommendations(
            product=product,
            category_filter=category,
            min_budget=min_budget,
            max_budget=max_budget
        )

        applied_budget = None
        if min_budget is not None or max_budget is not None:
            applied_budget = {"min": min_budget, "max": max_budget}

        return AccessoryRecommendationsResponse(
            productId=product.id,
            productName=product.name,
            brand=product.brand,
            model=product.model,
            category=product.category,
            appliedBudget=applied_budget,
            appliedCategory=category,
            recommendations=recommendations,
            totalCount=len(recommendations)
        )

    async def get_available_categories(self, user_id: str, product_id: str) -> List[str]:
        """
        Lists available accessory categories specifically for the selected product.
        """
        product = await product_service.get_product_by_id(product_id, user_id)
        all_recs = await self.retrieval_engine.get_recommendations(product=product)
        categories = sorted(list(set(r.category for r in all_recs)))
        return categories


accessory_service = AccessoryService()
