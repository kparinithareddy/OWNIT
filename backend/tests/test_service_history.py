import pytest
from datetime import datetime, timezone
from bson import ObjectId
from unittest.mock import AsyncMock, patch

from app.schemas.product import ProductResponse
from app.schemas.service_history import (
    ServiceRecordCreate,
    ServiceRecordUpdate,
    ServiceRecordResponse
)
from app.services.service_history_service import (
    service_history_service,
    format_service_doc
)
from app.services.timeline_service import timeline_service
from app.services.life_score_service import life_score_service
from app.services.context_builder import build_product_system_context
from app.core.exceptions import NotFoundException


@pytest.fixture
def mock_product():
    now = datetime.now(timezone.utc)
    return ProductResponse(
        id="prod-phone-01",
        userId="user-01",
        name="Galaxy S24 Ultra",
        brand="Samsung",
        model="SM-S928B",
        category="Mobile",
        purchaseDate="2026-02-01",
        price=129999.0,
        seller="Samsung Online Store",
        serialNumber="R5CW1234567",
        returnDuration="14 Days",
        returnDeadline="2026-02-15",
        returnStatus="Expired",
        returnDaysRemaining=-200,
        createdAt=now,
        updatedAt=now
    )


def test_format_service_doc():
    doc_id = ObjectId()
    doc = {
        "_id": doc_id,
        "productId": "prod-phone-01",
        "userId": "user-01",
        "serviceDate": "2026-06-15",
        "problem": "Display touch unresponsive on right edge",
        "serviceCenter": "Samsung Authorized Service Center Indiranagar",
        "workPerformed": "Screen digitizer replacement & calibration",
        "cost": 0.0,
        "warrantyCovered": True,
        "notes": "Job Sheet #JS-88219",
        "documentId": "doc-invoice-01",
        "documentName": "service_jobsheet.pdf",
        "createdAt": datetime.now(timezone.utc),
        "updatedAt": datetime.now(timezone.utc)
    }

    res = format_service_doc(doc)
    assert res.id == str(doc_id)
    assert res.problem == "Display touch unresponsive on right edge"
    assert res.serviceCenter == "Samsung Authorized Service Center Indiranagar"
    assert res.workPerformed == "Screen digitizer replacement & calibration"
    assert res.cost == 0.0
    assert res.warrantyCovered is True
    assert res.notes == "Job Sheet #JS-88219"
    assert res.documentName == "service_jobsheet.pdf"


def test_context_builder_includes_service_history(mock_product):
    """
    Requirement: Use service history as optional context for AI assistant.
    """
    service_records = [
        {
            "serviceDate": "2026-06-15",
            "problem": "Display touch unresponsive on right edge",
            "serviceCenter": "Samsung Authorized Service Center",
            "workPerformed": "Screen digitizer replacement",
            "cost": 0.0,
            "warrantyCovered": True,
            "notes": "Covered under panel warranty"
        }
    ]

    prompt, sources = build_product_system_context(
        product=mock_product,
        warranties=[],
        documents=[],
        maintenance_records=[],
        recommendations=[],
        service_records=service_records
    )

    assert "=== PAST SERVICE & REPAIR HISTORY ===" in prompt
    assert "Display touch unresponsive on right edge" in prompt
    assert "Samsung Authorized Service Center" in prompt
    assert "Screen digitizer replacement" in prompt
    assert "Yes (Warranty Claim)" in prompt


def test_life_score_incorporates_service_history(mock_product):
    """
    Requirement: Use service history as optional context for Product Life Score.
    """
    service_records = [
        {
            "serviceDate": "2026-06-15",
            "problem": "Battery degradation replacement",
            "serviceCenter": "Official Center",
            "workPerformed": "Installed new genuine battery module",
            "cost": 1500.0,
            "warrantyCovered": False
        }
    ]

    score_res = life_score_service.compute_score(
        product=mock_product,
        warranties=[],
        documents=[],
        maintenance_records=[],
        service_records=service_records
    )

    # Check that service logs contributed to Maintenance & Care factor
    maint_factor = next(f for f in score_res.factors if f.name == "Maintenance & Care")
    assert "Verified service history logged" in maint_factor.description
    assert any("service" in r.lower() for r in score_res.positiveReasons)
