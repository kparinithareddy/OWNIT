import pytest
from datetime import datetime, timezone
from bson import ObjectId

from app.services.ai.retrieval_service import IntentClassifier
from app.services.ai.source_service import source_service, VERIFIED_MANUFACTURER_PORTALS
from app.services.ai.prompt_service import prompt_service
from app.services.ai.assistant_service import assistant_service
from app.schemas.ai import AIAction, AIMessageSendRequest
from app.schemas.sources import SourceReference


def test_intent_classification():
    """
    Test deterministic intent classifier for user questions.
    """
    assert IntentClassifier.classify_intent("How many products do I have in total?") == "count_summary"
    assert IntentClassifier.classify_intent("Give me an overview of all my items") == "count_summary"
    assert IntentClassifier.classify_intent("Which warranties are expiring soon?") == "warranty"
    assert IntentClassifier.classify_intent("Is liquid damage covered by my warranty?") == "warranty"
    assert IntentClassifier.classify_intent("Can I return my Samsung TV?") == "return"
    assert IntentClassifier.classify_intent("What is my return window deadline?") == "return"
    assert IntentClassifier.classify_intent("How should I clean the screen?") == "maintenance"
    assert IntentClassifier.classify_intent("Show past repair and service history") == "service"
    assert IntentClassifier.classify_intent("Which device has the lowest life score?") == "life_score"
    assert IntentClassifier.classify_intent("Draft a warranty claim for customer support") == "claim"
    assert IntentClassifier.classify_intent("Show my uploaded invoices and bills") == "documents"
    assert IntentClassifier.classify_intent("Tell me a tech joke") == "general"


def test_source_service_4_tier_hierarchy():
    """
    Test source prioritization:
    1. User documents
    2. Official OEM portal
    3. Reliable seller return policy
    4. General preventive knowledge
    """
    product = {
        "name": "Galaxy S25 5G",
        "brand": "Samsung",
        "model": "SM-S928B",
        "category": "Mobile",
        "seller": "Samsung Online Store",
        "returnPolicySource": "Samsung 14-day official replacement policy",
        "returnDuration": "14 Days",
        "returnStatus": "Active"
    }
    warranties = [
        {
            "type": "Manufacturer Standard Warranty",
            "provider": "Samsung India",
            "startDate": "2026-08-10",
            "expiryDate": "2027-08-10",
            "status": "Active"
        }
    ]
    documents = [
        {"documentType": "Tax Invoice", "originalFilename": "samsung_s25_invoice.pdf", "uploadedAt": "2026-08-10"}
    ]

    sources = source_service.get_sources_for_product(product, warranties, documents)

    # Must contain 4 tiers
    source_types = [s.sourceType for s in sources]
    assert "user_document" in source_types
    assert "official_manufacturer" in source_types
    assert "reliable_external" in source_types
    assert "general_knowledge" in source_types

    # Check OEM verification
    oem_source = next(s for s in sources if s.sourceType == "official_manufacturer")
    assert oem_source.domain == "samsung.com"
    assert oem_source.verified is True
    assert "samsung.com" in oem_source.url


def test_global_system_prompt_builder():
    """
    Test Global OWNIT Assistant prompt generation with portfolio facts and injection protection.
    """
    portfolio_stats = {
        "totalProducts": 4,
        "totalValue": 125000.0,
        "totalWarranties": 5,
        "activeWarrantiesCount": 3,
        "expiringSoonWarrantiesCount": 1,
        "expiredWarrantiesCount": 1,
        "totalDocuments": 3,
        "totalMaintenanceRecords": 2,
        "totalServiceRecords": 1,
        "products": [
            {"id": "p1", "name": "Bravia 55 OLED", "brand": "Sony", "model": "XR-55A80L", "category": "TV", "price": 85000.0, "purchaseDate": "2026-01-10", "lifeScore": 92},
            {"id": "p2", "name": "Galaxy S25", "brand": "Samsung", "model": "SM-S928B", "category": "Mobile", "price": 40000.0, "purchaseDate": "2026-06-15", "lifeScore": 75}
        ],
        "expiringSoonWarranties": [
            {"productName": "Galaxy S25", "productBrand": "Samsung", "type": "Screen Protection", "expiryDate": "2026-09-25", "daysRemaining": 14, "provider": "Samsung Care"}
        ],
        "activeWarranties": [
            {"productName": "Bravia 55 OLED", "productBrand": "Sony", "type": "Panel Warranty", "expiryDate": "2028-01-10", "daysRemaining": 486}
        ],
        "expiredWarranties": [],
        "returnEligibleProducts": [],
        "lowestLifeScoreProducts": [
            {"name": "Galaxy S25", "brand": "Samsung", "lifeScore": 75, "category": "Mobile"}
        ]
    }

    prompt, sources = prompt_service.build_global_system_prompt(portfolio_stats, language="en")

    # Assert accurate grounding
    assert "Total Registered Assets: 4 item(s)" in prompt
    assert "₹125,000.00" in prompt
    assert "Bravia 55 OLED" in prompt
    assert "Galaxy S25" in prompt
    assert "Screen Protection expires on 2026-09-25 (14 days left" in prompt
    assert "Life Score: 75/100" in prompt
    assert "PROMPT INJECTION DEFENSE" in prompt
    assert "TRUTHFULNESS & GROUNDING" in prompt
    assert len(sources) >= 2


def test_offline_fallback_deterministic_generation():
    """
    Test deterministic response generation when local Ollama is offline.
    """
    portfolio_stats = {
        "totalProducts": 3,
        "totalValue": 95000.0,
        "totalWarranties": 3,
        "activeWarrantiesCount": 2,
        "expiringSoonWarrantiesCount": 1,
        "expiredWarrantiesCount": 0,
        "totalDocuments": 2,
        "totalMaintenanceRecords": 1,
        "totalServiceRecords": 0,
        "products": [
            {"id": "p-1", "name": "MacBook Air", "brand": "Apple", "model": "M3", "price": 95000.0, "purchaseDate": "2026-02-01", "lifeScore": 88}
        ],
        "expiringSoonWarranties": [
            {"productId": "p-1", "productName": "MacBook Air", "productBrand": "Apple", "type": "AppleCare+", "expiryDate": "2026-09-30", "daysRemaining": 19, "provider": "Apple"}
        ],
        "activeWarranties": [
            {"productId": "p-1", "productName": "MacBook Air", "productBrand": "Apple", "type": "AppleCare+", "expiryDate": "2026-09-30", "daysRemaining": 19}
        ],
        "expiredWarranties": [],
        "returnEligibleProducts": [],
        "lowestLifeScoreProducts": [
            {"id": "p-1", "name": "MacBook Air", "brand": "Apple", "lifeScore": 88, "category": "Laptop"}
        ]
    }

    # 1. Count query
    text, actions = assistant_service._generate_offline_fallback(
        intent="count_summary",
        context_type="global",
        portfolio_stats=portfolio_stats,
        product_data={},
        query="How many products do I have?"
    )
    assert "**3 product(s)**" in text
    assert "₹95,000.00" in text
    assert len(actions) > 0
    assert actions[0].actionType == "view_product"

    # 2. Expiring warranty query
    w_text, w_actions = assistant_service._generate_offline_fallback(
        intent="warranty",
        context_type="global",
        portfolio_stats=portfolio_stats,
        product_data={},
        query="Which warranties are expiring?"
    )
    assert "AppleCare+" in w_text
    assert "2026-09-30" in w_text
    assert len(w_actions) > 0
    assert w_actions[0].actionType == "view_warranty"

    # 3. Life score query
    ls_text, ls_actions = assistant_service._generate_offline_fallback(
        intent="life_score",
        context_type="global",
        portfolio_stats=portfolio_stats,
        product_data={},
        query="What is my lowest life score?"
    )
    assert "MacBook Air" in ls_text
    assert "88/100" in ls_text


def test_product_system_prompt_with_cross_product_awareness():
    """
    Test that product-specific prompt is anchored to target asset but retains global portfolio context.
    """
    product_data = {
        "product": {
            "_id": "prod-100",
            "name": "LG Front Load Washing Machine",
            "brand": "LG",
            "model": "FHM1408BDW",
            "category": "Washing Machine",
            "purchaseDate": "2025-05-10",
            "price": 38990.0,
            "seller": "Croma",
            "serialNumber": "LG-WM-88219",
            "lifeScore": 85,
            "returnDuration": "7 Days",
            "returnDeadline": "2025-05-17",
            "returnStatus": "Expired"
        },
        "warranties": [
            {
                "type": "Motor Inverter Warranty",
                "provider": "LG Electronics",
                "startDate": "2025-05-10",
                "expiryDate": "2035-05-10",
                "status": "Active",
                "daysRemaining": 3163,
                "benefits": ["Direct Drive Motor repair or replacement"],
                "exclusions": ["Commercial usage", "Tampering"]
            }
        ],
        "documents": [
            {"documentType": "Tax Invoice", "originalFilename": "croma_lg_bill.pdf", "uploadedAt": "2025-05-10"}
        ],
        "maintenanceRecords": [
            {"title": "Tub Clean Cycle", "type": "Cleaning", "date": "2026-08-01", "cost": 0, "status": "Completed"}
        ],
        "serviceRecords": []
    }

    portfolio_stats = {
        "totalProducts": 5,
        "totalWarranties": 6,
        "activeWarrantiesCount": 5,
        "expiringSoonWarrantiesCount": 0
    }

    prompt, sources = prompt_service.build_product_system_prompt(product_data, portfolio_stats, language="en")

    assert "LG Front Load Washing Machine" in prompt
    assert "FHM1408BDW" in prompt
    assert "LG-WM-88219" in prompt
    assert "Motor Inverter Warranty" in prompt
    assert "Direct Drive Motor" in prompt
    assert "Tub Clean Cycle" in prompt
    assert "GLOBAL PORTFOLIO SUMMARY" in prompt
    assert "Total Products: 5" in prompt
    assert len(sources) >= 2
