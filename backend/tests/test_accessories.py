import pytest
from app.schemas.product import ProductResponse
from app.services.accessory_service import VerifiedCatalogAccessoryService, accessory_service


@pytest.fixture
def samsung_tv_product():
    return ProductResponse(
        id="66dbb01234abcd5678ef9012",
        userId="66dbb01234abcd5678ef9099",
        name="Samsung 55\" Crystal 4K UHD TV",
        brand="Samsung",
        model="UA55DU8000",
        category="TV",
        purchaseDate="2025-01-15",
        price=54990.00,
        quantity=1,
        serialNumber="SN-UA55DU8000-XYZ",
        createdAt="2025-01-15T10:00:00Z",
        updatedAt="2025-01-15T10:00:00Z"
    )


@pytest.fixture
def washing_machine_product():
    return ProductResponse(
        id="66dbb01234abcd5678ef9013",
        userId="66dbb01234abcd5678ef9099",
        name="Samsung 8kg Front Load Washing Machine",
        brand="Samsung",
        model="WW80T504DAX1TL",
        category="Washing Machine",
        purchaseDate="2025-02-10",
        price=42990.00,
        quantity=1,
        serialNumber="SN-WW80T-123",
        createdAt="2025-02-10T10:00:00Z",
        updatedAt="2025-02-10T10:00:00Z"
    )


@pytest.mark.anyio
async def test_samsung_tv_accessories_all_categories(samsung_tv_product):
    engine = VerifiedCatalogAccessoryService()
    recs = await engine.get_recommendations(product=samsung_tv_product)

    assert len(recs) > 0
    categories = {r.category.lower() for r in recs}
    
    # Required categories from user prompt
    assert "soundbar" in categories
    assert "wall mount" in categories
    assert "hdmi cable" in categories
    assert "surge protector" in categories

    # Verify compatibility tiers exist
    compat_statuses = {r.compatibilityStatus for r in recs}
    assert "Compatible" in compat_statuses
    assert "Potentially compatible" in compat_statuses

    # Verify evidence and platform
    for r in recs:
        assert len(r.compatibilityReason) > 10
        assert r.platform is not None
        assert r.price > 0


@pytest.mark.anyio
async def test_budget_filtering_5k_to_10k(samsung_tv_product):
    engine = VerifiedCatalogAccessoryService()
    recs = await engine.get_recommendations(
        product=samsung_tv_product,
        min_budget=5000.0,
        max_budget=10000.0
    )

    assert len(recs) > 0
    for r in recs:
        assert 5000.0 <= r.price <= 10000.0
        assert r.inBudget is True


@pytest.mark.anyio
async def test_category_filtering(samsung_tv_product):
    engine = VerifiedCatalogAccessoryService()
    recs = await engine.get_recommendations(
        product=samsung_tv_product,
        category_filter="wall mount"
    )

    assert len(recs) > 0
    for r in recs:
        assert r.category.lower() == "wall mount"
        assert r.sourceUrl is not None


@pytest.mark.anyio
async def test_washing_machine_accessories(washing_machine_product):
    engine = VerifiedCatalogAccessoryService()
    recs = await engine.get_recommendations(product=washing_machine_product)

    assert len(recs) > 0
    categories = {r.category.lower() for r in recs}
    assert "stand" in categories or "filter" in categories or "cover" in categories
