import pytest
from datetime import datetime, timezone
from app.schemas.product import ProductResponse
from app.schemas.warranty import WarrantyResponse
from app.schemas.claim_assistant import (
    ClaimPreparationRequest,
    ClaimProvenanceType
)
from app.services.claim_assistant_service import claim_assistant_service
from unittest.mock import AsyncMock, patch


@pytest.fixture
def mock_laptop_product():
    now = datetime.now(timezone.utc)
    return ProductResponse(
        id="prod-laptop-01",
        userId="user-test-01",
        name="MacBook Pro 16",
        brand="Apple",
        model="MK183HN/A",
        category="Laptop",
        purchaseDate="2026-01-15",
        price=239900.0,
        seller="Apple Store BKC",
        serialNumber="C02G1234MD6R",
        returnDuration="14 Days",
        returnDeadline="2026-01-29",
        returnStatus="Expired",
        returnDaysRemaining=-220,
        createdAt=now,
        updatedAt=now
    )


@pytest.fixture
def mock_apple_warranty():
    now = datetime.now(timezone.utc)
    return [
        WarrantyResponse(
            id="w-applecare",
            productId="prod-laptop-01",
            userId="user-test-01",
            type="AppleCare+ Comprehensive",
            provider="Apple India",
            duration="3 Years",
            startDate="2026-01-15",
            expiryDate="2029-01-15",
            benefits="Unlimited accidental damage protection, battery replacement below 80%, logic board and Liquid Retina XDR screen",
            exclusions="Intentional damage, catastrophic damage, unauthorized modification",
            claimProcedure="Book Genius Bar appointment or authorized service provider",
            serviceInformation="000800 1009009 (Apple Support India)",
            status="Active",
            daysRemaining=850,
            statusColor="green",
            createdAt=now,
            updatedAt=now
        )
    ]


@pytest.mark.anyio
async def test_prepare_claim_dossier_complete_structure(mock_laptop_product, mock_apple_warranty):
    """
    Test: Claim preparation dossier includes all required sections,
    provenance distinctions, editable draft message, and review checklist.
    """
    with patch("app.services.product_service.product_service.get_product_by_id", new_callable=AsyncMock) as mock_get_prod, \
         patch("app.services.warranty_service.warranty_service.get_warranties_by_product", new_callable=AsyncMock) as mock_get_warr:

        mock_get_prod.return_value = mock_laptop_product
        mock_get_warr.return_value = mock_apple_warranty

        req = ClaimPreparationRequest(
            productId="prod-laptop-01",
            problemDescription="Battery draining rapidly and trackpad haptic feedback not clicking properly",
            problemStartDate="2026-09-01",
            incidentDetails="Ran Apple Diagnostics (error code PPT004 battery service recommended)"
        )

        res = await claim_assistant_service.prepare_claim_dossier("user-test-01", req)

        # 1. Verify Core Output Sections
        assert res.productId == "prod-laptop-01"
        assert res.brand == "Apple"
        assert len(res.productInfoFields) >= 4
        assert res.problemSummary is not None
        assert res.selectedWarranty is not None
        assert len(res.warrantyStatusFields) >= 2
        assert len(res.coverageFields) >= 1
        assert len(res.relevantExclusions) >= 1
        assert len(res.requiredDocuments) >= 4
        assert len(res.claimProcedureSteps) >= 4
        assert res.serviceContact["brand"] == "Apple"
        assert res.recommendedNextStep is not None
        assert len(res.draftSupportMessage) > 100
        assert len(res.confirmationChecklist) >= 4

        # 2. Verify Provenance Distinctions
        provenances = [f.provenance for f in res.productInfoFields] + [res.problemSummary.provenance] + [f.provenance for f in res.coverageFields]
        assert ClaimProvenanceType.DOCUMENT_VERIFIED in provenances
        assert ClaimProvenanceType.AI_GENERATED in provenances

        # 3. Verify Draft Support Message Content
        assert "AppleCare+ Comprehensive" in res.draftSupportMessage
        assert "C02G1234MD6R" in res.draftSupportMessage
        assert "Battery draining rapidly" in res.draftSupportMessage
        assert "Subject: Warranty Service Request" in res.draftSupportMessage

        # 4. Verify Non-automatic submission disclaimer
        assert "does NOT submit claims" in res.disclaimer
