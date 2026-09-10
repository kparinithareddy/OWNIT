import pytest
from datetime import datetime, timezone
from app.schemas.product import ProductResponse
from app.schemas.warranty import WarrantyResponse
from app.schemas.warranty_intelligence import (
    CoverageLikelihood,
    WarrantyQuestionType,
    WarrantyQuestionRequest
)
from app.services.warranty_intelligence_service import (
    warranty_intelligence_service,
    EXCLUSION_PATTERNS,
    INCLUSION_PATTERNS
)
from app.schemas.sources import SourceReference


@pytest.fixture
def mock_tv_product():
    now = datetime.now(timezone.utc)
    return ProductResponse(
        id="prod-tv-100",
        userId="user-test-01",
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


@pytest.fixture
def mock_active_warranties():
    now = datetime.now(timezone.utc)
    return [
        WarrantyResponse(
            id="w-comp-1",
            productId="prod-tv-100",
            userId="user-test-01",
            type="Comprehensive Warranty",
            provider="Samsung India",
            duration="1 Year",
            startDate="2026-08-10",
            expiryDate="2027-08-10",
            benefits="Full coverage for internal motherboards and power supply unit",
            exclusions="Physical screen cracks, External liquid spills",
            claimProcedure="Call Samsung toll-free customer support 1800-40-SAMSUNG",
            serviceInformation="1800-40-SAMSUNG",
            status="Active",
            daysRemaining=334,
            statusColor="green",
            createdAt=now,
            updatedAt=now
        ),
        WarrantyResponse(
            id="w-panel-1",
            productId="prod-tv-100",
            userId="user-test-01",
            type="Panel Warranty",
            provider="Samsung India",
            duration="3 Years",
            startDate="2026-08-10",
            expiryDate="2029-08-10",
            benefits="Direct replacement for LED panel manufacturing defects and vertical line glitches",
            exclusions="Accidental drops and blunt force impacts",
            claimProcedure="Schedule on-site technician visit",
            serviceInformation="1800-40-SAMSUNG",
            status="Active",
            daysRemaining=1064,
            statusColor="green",
            createdAt=now,
            updatedAt=now
        )
    ]


@pytest.fixture
def mock_expired_warranties():
    now = datetime.now(timezone.utc)
    return [
        WarrantyResponse(
            id="w-old-1",
            productId="prod-tv-100",
            userId="user-test-01",
            type="Comprehensive Warranty",
            provider="Samsung India",
            duration="1 Year",
            startDate="2024-01-10",
            expiryDate="2025-01-10",
            benefits="General parts and labor",
            exclusions="Physical damage",
            claimProcedure="Service center visit",
            serviceInformation="1800-40-SAMSUNG",
            status="Expired",
            daysRemaining=-500,
            statusColor="red",
            createdAt=now,
            updatedAt=now
        )
    ]


@pytest.fixture
def mock_sources():
    return [
        SourceReference(
            title="Uploaded Invoice (reliance_bill.pdf)",
            sourceType="user_document",
            domain=None,
            url=None,
            details="User vault document",
            verified=True
        ),
        SourceReference(
            title="Samsung Official Support",
            sourceType="official_manufacturer",
            domain="samsung.com",
            url="https://www.samsung.com/in/support/warranty/",
            details="Standard OEM terms",
            verified=True
        )
    ]


def test_issue_coverage_manufacturing_defect_likely_or_confirmed(mock_tv_product, mock_active_warranties, mock_sources):
    """
    Test: Internal screen panel defect during active warranty period -> Likely or Confirmed coverage.
    """
    res = warranty_intelligence_service._analyze_specific_issue(
        product=mock_tv_product,
        warranties=mock_active_warranties,
        documents=[{"documentType": "Purchase Invoice", "originalFilename": "bill.pdf"}],
        sources=mock_sources,
        issue_text="Screen has vertical line and is flickering"
    )

    assert res.coverageLikelihood in [CoverageLikelihood.LIKELY, CoverageLikelihood.CONFIRMED]
    assert res.isWarrantyActive is True
    assert res.statusColor in ["green", "blue"]
    assert len(res.matchingInclusions) > 0

    # Non-guaranteeing language assertions
    assert "final coverage is determined by the manufacturer/service center" in res.explanation.lower()
    assert "according to your" in res.explanation.lower() or "based on the available information" in res.explanation.lower()
    assert len(res.claimSteps) > 0
    assert res.supportContact == "1800-40-SAMSUNG"
    assert len(res.pipelineSteps) == 9


def test_issue_coverage_physical_or_liquid_damage_excluded(mock_tv_product, mock_active_warranties, mock_sources):
    """
    Test: Water spill or dropped TV -> Excluded issue.
    """
    res = warranty_intelligence_service._analyze_specific_issue(
        product=mock_tv_product,
        warranties=mock_active_warranties,
        documents=[],
        sources=mock_sources,
        issue_text="Dropped during cleaning and water spilled on the panel"
    )

    assert res.coverageLikelihood == CoverageLikelihood.EXCLUDED
    assert res.statusColor == "red"
    assert len(res.matchingExclusions) >= 1
    assert "final coverage is determined by the manufacturer/service center" in res.explanation.lower()
    assert "excluded" in res.explanation.lower()


def test_issue_coverage_expired_warranty(mock_tv_product, mock_expired_warranties, mock_sources):
    """
    Test: Defect reported on expired warranty -> Excluded (Warranty Expired).
    """
    res = warranty_intelligence_service._analyze_specific_issue(
        product=mock_tv_product,
        warranties=mock_expired_warranties,
        documents=[],
        sources=mock_sources,
        issue_text="TV won't turn on automatically"
    )

    assert res.coverageLikelihood == CoverageLikelihood.EXCLUDED
    assert res.statusColor == "red"
    assert "expired" in res.explanation.lower()
    assert "final coverage is determined by the manufacturer/service center" in res.explanation.lower()


def test_issue_coverage_ambiguous_issue_unclear(mock_tv_product, mock_active_warranties, mock_sources):
    """
    Test: Vague/ambiguous symptom -> Unclear coverage.
    """
    res = warranty_intelligence_service._analyze_specific_issue(
        product=mock_tv_product,
        warranties=mock_active_warranties,
        documents=[],
        sources=mock_sources,
        issue_text="Something feels weird when I use the remote controller app"
    )

    assert res.coverageLikelihood == CoverageLikelihood.UNCLEAR
    assert res.statusColor == "amber"
    assert "final coverage is determined by the manufacturer/service center" in res.explanation.lower()


def test_standard_query_is_active(mock_tv_product, mock_active_warranties, mock_sources):
    """
    Test standard question: Is my warranty active?
    """
    res = warranty_intelligence_service._handle_is_active(
        product=mock_tv_product,
        warranties=mock_active_warranties,
        documents=[],
        sources=mock_sources
    )

    assert res.isWarrantyActive is True
    assert res.coverageLikelihood == CoverageLikelihood.CONFIRMED
    assert res.statusLabel == "Warranty Active"
    assert "ACTIVE" in res.explanation


def test_standard_query_what_excluded(mock_tv_product, mock_active_warranties, mock_sources):
    """
    Test standard question: What is excluded?
    """
    res = warranty_intelligence_service._handle_what_excluded(
        product=mock_tv_product,
        warranties=mock_active_warranties,
        documents=[],
        sources=mock_sources
    )

    assert len(res.matchingExclusions) > 0
    assert res.coverageLikelihood == CoverageLikelihood.EXCLUDED
    assert "EXCLUDED" in res.explanation


def test_standard_query_required_documents(mock_tv_product, mock_active_warranties, mock_sources):
    """
    Test standard question: Which documents do I need?
    """
    docs = [{"documentType": "Purchase Invoice", "originalFilename": "invoice.pdf"}]
    res = warranty_intelligence_service._handle_required_documents(
        product=mock_tv_product,
        warranties=mock_active_warranties,
        documents=docs,
        sources=mock_sources
    )

    assert len(res.requiredDocuments) >= 4
    assert len(res.documentsAvailableInVault) >= 1
    assert len(res.missingDocuments) >= 1
    assert "1 of 4" in res.explanation
