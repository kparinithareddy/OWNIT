import pytest
from datetime import datetime, timezone, timedelta
from app.schemas.product import ProductCreate
from app.services.product_service import product_service
from app.services.warranty_service import warranty_service
from app.schemas.warranty import WarrantyCreate
from app.services.maintenance_service import maintenance_service
from app.schemas.maintenance import MaintenanceCreate


from app.core.database import db_manager


@pytest.mark.anyio
async def test_search_and_filter_products_full_suite():
    is_connected = await db_manager.connect()
    if not is_connected:
        pytest.skip("MongoDB service is offline in the test environment.")

    test_user = "66dbb01234abcd5678ef9888"

    # Clean up test user records
    await product_service.collection.delete_many({"userId": test_user})
    await product_service.db["warranties"].delete_many({"userId": test_user})
    await product_service.db["maintenance_records"].delete_many({"userId": test_user})

    today = datetime.now(timezone.utc).date()
    today_str = today.isoformat()

    # Create Product 1: Apple MacBook Pro (Active return, active warranty, no maintenance)
    p1 = await product_service.create_product(
        user_id=test_user,
        data=ProductCreate(
            name="MacBook Pro 16",
            brand="Apple",
            model="MK183HN/A",
            category="Laptop",
            purchaseDate=today_str,
            price=220000.0,
            serialNumber="C02G1234ABCD",
            returnDuration="14 Days",
            returnStartDate=today_str
        )
    )

    # Attach Active Warranty (1 year from now)
    w1_exp = (today + timedelta(days=365)).isoformat()
    await warranty_service.create_warranty(
        user_id=test_user,
        data=WarrantyCreate(
            productId=p1.id,
            provider="AppleCare+",
            type="Manufacturer",
            startDate=today_str,
            expiryDate=w1_exp,
            durationMonths=12
        )
    )

    # Create Product 2: Samsung Galaxy S24 (Expired return, expiring soon warranty, due maintenance)
    past_date = (today - timedelta(days=350)).isoformat()
    p2 = await product_service.create_product(
        user_id=test_user,
        data=ProductCreate(
            name="Galaxy S24 Ultra",
            brand="Samsung",
            model="SM-S928B",
            category="Mobile",
            purchaseDate=past_date,
            price=129999.0,
            serialNumber="R5CW1234XYZ",
            returnDuration="7 Days",
            returnStartDate=past_date
        )
    )

    # Attach Expiring Soon Warranty (15 days from now)
    w2_exp = (today + timedelta(days=15)).isoformat()
    await warranty_service.create_warranty(
        user_id=test_user,
        data=WarrantyCreate(
            productId=p2.id,
            provider="Samsung India",
            type="Manufacturer",
            startDate=past_date,
            expiryDate=w2_exp,
            durationMonths=12
        )
    )

    # Attach Due Maintenance Record
    m_due = (today + timedelta(days=2)).isoformat()
    await maintenance_service.create_record(
        user_id=test_user,
        data=MaintenanceCreate(
            productId=p2.id,
            title="Clean USB Port",
            date=today_str,
            nextDueDate=m_due,
            status="Scheduled",
            type="Cleaning"
        )
    )

    # Create Product 3: Sony Bravia OLED (Expired return, expired warranty, overdue maintenance)
    old_date = (today - timedelta(days=800)).isoformat()
    p3 = await product_service.create_product(
        user_id=test_user,
        data=ProductCreate(
            name="Bravia XR OLED 55",
            brand="Sony",
            model="XR-55A80L",
            category="TV",
            purchaseDate=old_date,
            price=145000.0,
            serialNumber="SONY-XR-999888",
            returnDuration="10 Days",
            returnStartDate=old_date
        )
    )

    # Attach Expired Warranty (expired 400 days ago)
    w3_exp = (today - timedelta(days=400)).isoformat()
    await warranty_service.create_warranty(
        user_id=test_user,
        data=WarrantyCreate(
            productId=p3.id,
            provider="Sony India",
            type="Manufacturer",
            startDate=old_date,
            expiryDate=w3_exp,
            durationMonths=12
        )
    )

    # Attach Overdue Maintenance Record
    m_overdue = (today - timedelta(days=10)).isoformat()
    await maintenance_service.create_record(
        user_id=test_user,
        data=MaintenanceCreate(
            productId=p3.id,
            title="Screen dusting",
            date=old_date,
            nextDueDate=m_overdue,
            status="Pending",
            type="Routine Servicing"
        )
    )

    # 1. Test Search by Name
    res = await product_service.get_user_products(user_id=test_user, search="MacBook")
    assert len(res) == 1
    assert res[0].id == p1.id

    # 2. Test Search by Model
    res = await product_service.get_user_products(user_id=test_user, search="SM-S928B")
    assert len(res) == 1
    assert res[0].id == p2.id

    # 3. Test Search by Serial Number
    res = await product_service.get_user_products(user_id=test_user, search="SONY-XR-999888")
    assert len(res) == 1
    assert res[0].id == p3.id

    # 4. Test Search by Brand
    res = await product_service.get_user_products(user_id=test_user, search="Samsung")
    assert len(res) == 1
    assert res[0].id == p2.id

    # 5. Test Category Filter
    res = await product_service.get_user_products(user_id=test_user, category="Laptop")
    assert len(res) == 1
    assert res[0].id == p1.id

    # 6. Test Brand Filter
    res = await product_service.get_user_products(user_id=test_user, brand="Sony")
    assert len(res) == 1
    assert res[0].id == p3.id

    # 7. Test Warranty Status: Active
    res = await product_service.get_user_products(user_id=test_user, warranty_status="active")
    assert len(res) == 1
    assert res[0].id == p1.id

    # 8. Test Warranty Status: Expiring Soon
    res = await product_service.get_user_products(user_id=test_user, warranty_status="expiring_soon")
    assert len(res) == 1
    assert res[0].id == p2.id

    # 9. Test Warranty Status: Expired
    res = await product_service.get_user_products(user_id=test_user, warranty_status="expired")
    assert len(res) == 1
    assert res[0].id == p3.id

    # 10. Test Return Status: Active
    res = await product_service.get_user_products(user_id=test_user, return_status="active")
    assert len(res) == 1
    assert res[0].id == p1.id

    # 11. Test Return Status: Expired
    res = await product_service.get_user_products(user_id=test_user, return_status="expired")
    assert len(res) == 2
    res_ids = {p.id for p in res}
    assert p2.id in res_ids
    assert p3.id in res_ids

    # 12. Test Maintenance Status: Due
    res = await product_service.get_user_products(user_id=test_user, maintenance_status="due")
    assert len(res) == 1
    assert res[0].id == p2.id

    # 13. Test Maintenance Status: Overdue
    res = await product_service.get_user_products(user_id=test_user, maintenance_status="overdue")
    assert len(res) == 1
    assert res[0].id == p3.id

    # 14. Test get_user_brands
    brands = await product_service.get_user_brands(user_id=test_user)
    assert "Apple" in brands
    assert "Samsung" in brands
    assert "Sony" in brands

    # Cleanup
    await product_service.collection.delete_many({"userId": test_user})
    await product_service.db["warranties"].delete_many({"userId": test_user})
    await product_service.db["maintenance_records"].delete_many({"userId": test_user})
