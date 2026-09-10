import pytest
from datetime import datetime, timezone
from app.schemas.product import ProductResponse
from app.schemas.warranty import WarrantyResponse
from app.services.context_builder import build_product_system_context


def test_context_builder_rich_synthesis_and_anti_hallucination_rules():
    """
    Requirement:
    - Product context provided to AI:
      name, brand, model, category, purchase date, warranty info, benefits, exclusions,
      uploaded documents, maintenance history, recommendations.
    - AI must not invent warranty coverage.
    - Never claim manufacturer information unless actually sourced.
    """
    now = datetime.now(timezone.utc)
    product = ProductResponse(
        id="prod-tv-01",
        userId="user-01",
        name="Samsung Crystal 4K UHD TV",
        brand="Samsung",
        model="UA55DU8000",
        category="TV",
        purchaseDate="2026-08-10",
        price=47990.0,
        seller="Reliance Digital",
        serialNumber="SAMS-55DU-9481",
        returnDuration="7 Days",
        returnDeadline="2026-08-17",
        returnStatus="Expired",
        returnDaysRemaining=-24,
        createdAt=now,
        updatedAt=now
    )

    warranties = [
        WarrantyResponse(
            id="w-comp",
            productId="prod-tv-01",
            userId="user-01",
            type="Comprehensive Warranty",
            provider="Samsung India",
            duration="1 Year",
            startDate="2026-08-10",
            expiryDate="2027-08-10",
            benefits="Full coverage for internal motherboards and power supply unit",
            exclusions="Physical screen cracks, External liquid spills",
            claimProcedure="Call Samsung toll-free customer support",
            serviceInformation="1800-40-SAMSUNG",
            status="Active",
            daysRemaining=334,
            statusColor="green",
            createdAt=now,
            updatedAt=now
        ),
        WarrantyResponse(
            id="w-panel",
            productId="prod-tv-01",
            userId="user-01",
            type="Panel Warranty",
            provider="Samsung India",
            duration="3 Years",
            startDate="2026-08-10",
            expiryDate="2029-08-10",
            benefits="Direct replacement for LED panel manufacturing defects",
            exclusions="Accidental drops",
            status="Active",
            daysRemaining=1064,
            statusColor="green",
            createdAt=now,
            updatedAt=now
        )
    ]

    documents = [
        {"documentType": "Purchase Bill", "originalFilename": "reliance_tv_bill.pdf", "uploadedAt": "2026-08-10"},
        {"documentType": "Warranty Card", "originalFilename": "samsung_warranty_card.pdf", "uploadedAt": "2026-08-10"}
    ]

    maintenance_records = [
        {
            "status": "Completed",
            "title": "Wall Mount Installation & Demo",
            "type": "Inspection",
            "date": "2026-08-12",
            "serviceProvider": "Samsung Authorized Engineer",
            "cost": 0.0
        }
    ]

    recommendations = [
        {
            "title": "Clean Screen with Microfiber Cloth",
            "description": "Never spray liquid cleaners directly on the screen panel.",
            "suggestedIntervalMonths": 1,
            "source": "General Display Care Guide",
            "disclaimer": "General preventive care guideline. Consult user manual."
        }
    ]

    system_prompt, sources = build_product_system_context(
        product=product,
        warranties=warranties,
        documents=documents,
        maintenance_records=maintenance_records,
        recommendations=recommendations
    )

    # 1. Verify all contextual fields present
    assert "Samsung Crystal 4K UHD TV" in system_prompt
    assert "UA55DU8000" in system_prompt
    assert "SAMS-55DU-9481" in system_prompt
    assert "Reliance Digital" in system_prompt
    assert "Comprehensive Warranty" in system_prompt
    assert "Panel Warranty" in system_prompt
    assert "Physical screen cracks" in system_prompt
    assert "reliance_tv_bill.pdf" in system_prompt
    assert "Wall Mount Installation & Demo" in system_prompt

    # 2. Verify strict anti-hallucination instruction & source hierarchy
    assert "SOURCE PRIORITY HIERARCHY" in system_prompt
    assert "DO NOT FABRICATE SOURCES OR URLS" in system_prompt
    assert "cannot verify" in system_prompt.lower()
    assert "UNVERIFIED INFORMATION" in system_prompt

    # 3. Verify sources list (SourceReference objects)
    source_titles = [s.title for s in sources]
    assert any("Comprehensive Warranty" in t for t in source_titles)
    assert any("Purchase Bill" in t for t in source_titles)
    assert any("Samsung Official Support" in t for t in source_titles)
    assert any("General Consumer Electronics" in t for t in source_titles)


def test_format_chat_message_with_source_references():
    from app.services.chat_service import format_chat_message
    from bson import ObjectId

    doc = {
        "_id": ObjectId(),
        "role": "assistant",
        "content": "According to your warranty card, panel replacement is covered.",
        "sources": ["Samsung India Official Warranty Policy"],
        "sourceReferences": [
            {
                "title": "Samsung Official Support (Samsung Official Support & Warranty Portal)",
                "sourceType": "official_manufacturer",
                "domain": "samsung.com",
                "url": "https://www.samsung.com/in/support/warranty/",
                "details": "Standard OEM terms",
                "verified": True
            }
        ],
        "createdAt": datetime.now(timezone.utc)
    }

    msg = format_chat_message(doc)
    assert msg.role == "assistant"
    assert len(msg.sourceReferences) == 1
    assert msg.sourceReferences[0].domain == "samsung.com"
    assert msg.sourceReferences[0].sourceType == "official_manufacturer"
    assert msg.sourceReferences[0].url == "https://www.samsung.com/in/support/warranty/"

