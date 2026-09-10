import pytest
from datetime import datetime, timezone
from app.schemas.product import ProductResponse
from app.schemas.warranty import WarrantyResponse
from app.services.retrieval_service import retrieval_service, VERIFIED_MANUFACTURER_PORTALS


def test_retrieval_service_hierarchy_ranking():
    """
    Requirement:
    Priority:
    1. Uploaded user documents
    2. Official manufacturer sources
    3. Reliable external sources
    4. General AI knowledge
    """
    now = datetime.now(timezone.utc)
    product = ProductResponse(
        id="prod-phone-01",
        userId="user-01",
        name="Galaxy S24 Ultra",
        brand="Samsung",
        model="SM-S928B",
        category="Mobile",
        purchaseDate="2026-08-10",
        price=129999.0,
        seller="Amazon India",
        returnDuration="7 Days",
        returnDeadline="2026-08-17",
        returnPolicySource="Amazon India Standard Replacement Policy",
        returnStatus="Expired",
        createdAt=now,
        updatedAt=now
    )

    warranties = [
        WarrantyResponse(
            id="w-comp",
            productId="prod-phone-01",
            userId="user-01",
            type="Comprehensive Warranty",
            provider="Samsung India",
            duration="1 Year",
            startDate="2026-08-10",
            expiryDate="2027-08-10",
            status="Active",
            daysRemaining=334,
            statusColor="green",
            createdAt=now,
            updatedAt=now
        )
    ]

    documents = [
        {"documentType": "Purchase Bill", "originalFilename": "amazon_invoice.pdf"},
        {"documentType": "Warranty Card", "originalFilename": "samsung_care_plus.pdf"}
    ]

    sources = retrieval_service.retrieve_hierarchical_sources(
        product=product,
        warranties=warranties,
        documents=documents,
        maintenance_records=[]
    )

    # Verify 4-tier structure
    source_types = [s.sourceType for s in sources]
    assert "user_document" in source_types
    assert "official_manufacturer" in source_types
    assert "reliable_external" in source_types
    assert "general_knowledge" in source_types

    # First sources must be user documents (Tier 1)
    assert sources[0].sourceType == "user_document"
    assert "amazon_invoice.pdf" in sources[0].title or "samsung_care_plus.pdf" in sources[0].title

    # Manufacturer source must have verified real domain (Tier 2)
    oem_source = next(s for s in sources if s.sourceType == "official_manufacturer")
    assert oem_source.domain == "samsung.com"
    assert "samsung.com" in oem_source.url
    assert oem_source.verified is True

    # Seller policy must be Tier 3
    seller_source = next(s for s in sources if s.sourceType == "reliable_external")
    assert "Amazon India" in seller_source.title
    assert seller_source.verified is True


def test_retrieval_service_unknown_brand_no_fake_urls():
    """
    Requirement:
    - Do not fabricate URLs or sources.
    - If information cannot be verified, clearly tell the user.
    """
    now = datetime.now(timezone.utc)
    product = ProductResponse(
        id="prod-unknown-01",
        userId="user-01",
        name="Custom Assembled Desk",
        brand="Local Carpenter Co",
        model="DESK-01",
        category="Other",
        purchaseDate="2026-08-10",
        price=8500.0,
        createdAt=now,
        updatedAt=now
    )

    sources = retrieval_service.retrieve_hierarchical_sources(
        product=product,
        warranties=[],
        documents=[],
        maintenance_records=[]
    )

    # Must NOT invent an OEM domain or fake website for an unknown brand
    oem_sources = [s for s in sources if s.sourceType == "official_manufacturer"]
    assert len(oem_sources) == 0

    # Only general knowledge should be returned when no documents or verified OEM exists
    assert any(s.sourceType == "general_knowledge" for s in sources)
