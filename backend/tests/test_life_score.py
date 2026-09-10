import pytest
from datetime import datetime, timezone, timedelta
from app.schemas.product import ProductResponse
from app.schemas.warranty import WarrantyResponse
from app.schemas.life_score import LifeScoreResponse, LifeScoreFactor
from app.services.life_score_service import life_score_service


def test_life_score_high_completeness():
    today = datetime.now(timezone.utc)
    purchase_date = (today - timedelta(days=60)).strftime("%Y-%m-%d")

    product = ProductResponse(
        id="prod-1",
        userId="user-1",
        name="MacBook Pro 16",
        brand="Apple",
        model="M3 Max",
        category="Laptop",
        purchaseDate=purchase_date,
        price=249900.0,
        quantity=1,
        seller="Apple Store BKC",
        serialNumber="C02G1234MD6R",
        returnStatus="Expired",
        returnDaysRemaining=-46,
        createdAt=today,
        updatedAt=today
    )

    warranties = [
        WarrantyResponse(
            id="w-1",
            productId="prod-1",
            userId="user-1",
            type="Comprehensive Warranty",
            provider="AppleCare+",
            duration="3 Years",
            startDate=purchase_date,
            expiryDate=(today + timedelta(days=700)).strftime("%Y-%m-%d"),
            status="Active",
            daysRemaining=700,
            statusColor="green",
            createdAt=today,
            updatedAt=today
        ),
        WarrantyResponse(
            id="w-2",
            productId="prod-1",
            userId="user-1",
            type="Accidental Damage Protection",
            provider="AppleCare+",
            duration="3 Years",
            startDate=purchase_date,
            expiryDate=(today + timedelta(days=700)).strftime("%Y-%m-%d"),
            status="Active",
            daysRemaining=700,
            statusColor="green",
            createdAt=today,
            updatedAt=today
        )
    ]

    documents = [
        {"documentType": "Purchase Bill", "originalFilename": "apple_invoice.pdf"},
        {"documentType": "Warranty Card", "originalFilename": "applecare_cert.pdf"},
        {"documentType": "User Manual", "originalFilename": "macbook_manual.pdf"}
    ]

    maintenance_records = [
        {"status": "Completed", "type": "Inspection", "title": "Initial Diagnostics"}
    ]

    score_res = life_score_service.compute_score(
        product=product,
        warranties=warranties,
        documents=documents,
        maintenance_records=maintenance_records
    )

    assert score_res.productId == "prod-1"
    assert score_res.score >= 85
    assert score_res.grade in ["Excellent", "Good"]
    assert score_res.color == "green"
    assert len(score_res.positiveReasons) >= 3
    assert len(score_res.factors) == 5
    # Transparency check: non-predictive disclaimer present
    assert "not a scientifically predictive" in score_res.disclaimer.lower()


def test_life_score_aged_with_expired_warranty_and_overdue_maint():
    today = datetime.now(timezone.utc)
    purchase_date = (today - timedelta(days=1200)).strftime("%Y-%m-%d")

    product = ProductResponse(
        id="prod-2",
        userId="user-1",
        name="Old Washing Machine",
        brand="Generic",
        model="WM-100",
        category="Washing Machine",
        purchaseDate=purchase_date,
        price=15000.0,
        quantity=1,
        serialNumber=None,
        createdAt=today,
        updatedAt=today
    )

    warranties = [
        WarrantyResponse(
            id="w-old",
            productId="prod-2",
            userId="user-1",
            type="Standard Warranty",
            provider="Brand",
            duration="1 Year",
            startDate=purchase_date,
            expiryDate=(today - timedelta(days=800)).strftime("%Y-%m-%d"),
            status="Expired",
            daysRemaining=-800,
            statusColor="red",
            createdAt=today,
            updatedAt=today
        )
    ]

    documents = [] # No documents

    maintenance_records = [
        {"status": "Overdue", "type": "Filter Replacement", "title": "Drum Clean Overdue"}
    ]

    score_res = life_score_service.compute_score(
        product=product,
        warranties=warranties,
        documents=documents,
        maintenance_records=maintenance_records
    )

    assert score_res.productId == "prod-2"
    assert score_res.score < 50
    assert score_res.grade == "Needs Attention"
    assert score_res.color == "red"
    # Actionable improvement tips should guide the user
    assert len(score_res.improvementTips) >= 2
    assert any("overdue" in tip.lower() for tip in score_res.improvementTips)


def test_life_score_transparency_factors_and_disclaimer():
    """
    Requirement:
    - Transparent rule-based score.
    - Do NOT claim this is scientifically predictive.
    - Factors: warranty, age, document completeness, maintenance, service history, deadlines.
    - Score: 0-100.
    """
    today = datetime.now(timezone.utc)
    product = ProductResponse(
        id="prod-3",
        userId="user-1",
        name="Sony Bravia TV",
        brand="Sony",
        model="KD-55X74K",
        category="TV",
        purchaseDate="2026-01-15",
        price=54990.0,
        seller="Croma",
        serialNumber="SN-89410",
        createdAt=today,
        updatedAt=today
    )

    score_res = life_score_service.compute_score(
        product=product,
        warranties=[],
        documents=[{"documentType": "Purchase Bill"}],
        maintenance_records=[]
    )

    assert 0 <= score_res.score <= 100
    factor_names = [f.name for f in score_res.factors]
    assert "Warranty & Coverage" in factor_names
    assert "Document Completeness" in factor_names
    assert "Maintenance & Care" in factor_names
    assert "Product Age" in factor_names
    assert "Asset Identifiers & Records" in factor_names
    assert "predictive" in score_res.disclaimer
