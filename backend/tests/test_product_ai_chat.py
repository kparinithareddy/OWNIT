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

    # 2. Verify strict anti-hallucination instruction
    assert "NO HALLUCINATED WARRANTIES" in system_prompt
    assert "cannot verify warranty coverage" in system_prompt.lower()
    assert "SOURCING TRANSPARENCY" in system_prompt

    # 3. Verify sources list
    assert any("Comprehensive Warranty" in s for s in sources)
    assert any("Purchase Bill" in s for s in sources)
    assert any("Product Record" in s for s in sources)
