import pytest
from app.schemas.product import ProductResponse
from app.services.recall_service import (
    VerifiedSafetyRecallService,
    STANDARD_ADVISORY_WORDING
)


@pytest.fixture
def macbook_pro_affected_serial():
    return ProductResponse(
        id="66dbb01234abcd5678ef9001",
        userId="66dbb01234abcd5678ef9099",
        name="Apple 15-inch MacBook Pro",
        brand="Apple",
        model="A1398 Mid 2015",
        category="Laptop",
        purchaseDate="2016-03-15",
        price=189900.00,
        quantity=1,
        serialNumber="C02SX000H03M",
        createdAt="2016-03-15T10:00:00Z",
        updatedAt="2016-03-15T10:00:00Z"
    )


@pytest.fixture
def macbook_pro_unaffected_serial():
    return ProductResponse(
        id="66dbb01234abcd5678ef9002",
        userId="66dbb01234abcd5678ef9099",
        name="Apple 15-inch MacBook Pro",
        brand="Apple",
        model="MacBook Pro 15-inch Mid 2015",
        category="Laptop",
        purchaseDate="2016-03-15",
        price=189900.00,
        quantity=1,
        serialNumber="F4KZX999ABCD",  # Does not match the C02/C2V/W8 regex
        createdAt="2016-03-15T10:00:00Z",
        updatedAt="2016-03-15T10:00:00Z"
    )


@pytest.fixture
def clean_product_no_recalls():
    return ProductResponse(
        id="66dbb01234abcd5678ef9003",
        userId="66dbb01234abcd5678ef9099",
        name="Logitech MX Master 3S Mouse",
        brand="Logitech",
        model="MX Master 3S",
        category="Peripherals",
        purchaseDate="2024-01-10",
        price=8995.00,
        quantity=1,
        serialNumber="LZ2024991100",
        createdAt="2024-01-10T10:00:00Z",
        updatedAt="2024-01-10T10:00:00Z"
    )


@pytest.fixture
def samsung_washer_product():
    return ProductResponse(
        id="66dbb01234abcd5678ef9004",
        userId="66dbb01234abcd5678ef9099",
        name="Samsung Top Load Washer",
        brand="Samsung",
        model="WA50K8600",
        category="Washing Machine",
        purchaseDate="2015-08-20",
        price=45000.00,
        quantity=1,
        serialNumber="WA50K860012345",
        createdAt="2015-08-20T10:00:00Z",
        updatedAt="2015-08-20T10:00:00Z"
    )


@pytest.mark.anyio
async def test_macbook_pro_affected_serial_match(macbook_pro_affected_serial):
    service = VerifiedSafetyRecallService()
    result = await service.check_product_recall(macbook_pro_affected_serial)

    assert result.hasPossibleRecall is True
    assert result.warningMessage == STANDARD_ADVISORY_WORDING
    assert "Possible recall match — verify with the official source." in result.warningMessage
    assert len(result.matches) > 0

    match = result.matches[0]
    assert match.affectedBrand == "Apple"
    assert match.isSerialMatched is True
    assert "support.apple.com" in match.sourceUrl
    assert "Apple Authorized Service Provider" in match.recommendedAction
    assert match.severity == "CRITICAL"


@pytest.mark.anyio
async def test_macbook_pro_unaffected_serial_eval(macbook_pro_unaffected_serial):
    service = VerifiedSafetyRecallService()
    result = await service.check_product_recall(macbook_pro_unaffected_serial)

    assert result.hasPossibleRecall is True
    assert len(result.matches) > 0
    match = result.matches[0]
    # Serial provided but does not match affected range
    assert match.isSerialMatched is False


@pytest.mark.anyio
async def test_product_with_no_recalls(clean_product_no_recalls):
    service = VerifiedSafetyRecallService()
    result = await service.check_product_recall(clean_product_no_recalls)

    assert result.hasPossibleRecall is False
    assert result.warningMessage is None
    assert len(result.matches) == 0


@pytest.mark.anyio
async def test_samsung_washer_safety_bulletin(samsung_washer_product):
    service = VerifiedSafetyRecallService()
    result = await service.check_product_recall(samsung_washer_product)

    assert result.hasPossibleRecall is True
    assert result.warningMessage == "Possible recall match — verify with the official source."
    assert len(result.matches) > 0
    match = result.matches[0]
    assert match.affectedBrand == "Samsung"
    assert "samsung.com" in match.sourceDomain
    assert match.severity == "CRITICAL"
