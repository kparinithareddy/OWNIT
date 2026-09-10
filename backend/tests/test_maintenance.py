import pytest
from app.schemas.maintenance import (
    MaintenanceCreate,
    MaintenanceUpdate,
    MaintenanceResponse,
    MaintenanceRecommendation
)
from app.services.maintenance_service import CATEGORY_RECOMMENDATIONS


def test_maintenance_create_and_response_schema():
    create_dto = MaintenanceCreate(
        productId="prod-101",
        title="Deep Cleaning & Filter Replacement",
        description="Rinsed dust mesh and replaced deodorizing filter cartridge.",
        date="2026-08-10",
        type="Filter Replacement",
        status="Completed",
        notes="Performed by authorized technician.",
        cost=850.0,
        serviceProvider="Samsung Care",
        nextDueDate="2026-11-10"
    )
    assert create_dto.productId == "prod-101"
    assert create_dto.type == "Filter Replacement"
    assert create_dto.cost == 850.0
    assert create_dto.nextDueDate == "2026-11-10"


def test_maintenance_recommendations_sourcing_and_disclaimer():
    """
    Requirement: Do not pretend that maintenance recommendations are manufacturer-approved unless sourced.
    """
    ac_recs = CATEGORY_RECOMMENDATIONS.get("Air Conditioner", [])
    assert len(ac_recs) > 0

    for rec in ac_recs:
        recommendation = MaintenanceRecommendation(**rec)
        assert recommendation.source != ""
        assert recommendation.disclaimer != ""
        # Not claiming unverified OEM endorsement
        assert recommendation.isManufacturerApproved is False
        assert "disclaimer" in recommendation.disclaimer.lower() or "general" in recommendation.disclaimer.lower()


def test_maintenance_recommendations_for_different_categories():
    assert "Washing Machine" in CATEGORY_RECOMMENDATIONS
    assert "Refrigerator" in CATEGORY_RECOMMENDATIONS
    assert "Laptop" in CATEGORY_RECOMMENDATIONS
    assert "Mobile" in CATEGORY_RECOMMENDATIONS
