import pytest
from datetime import date, timedelta
from app.schemas.notification import NotificationType
from app.services.notification_service import determine_eligible_notifications


def test_future_warranty_no_notifications():
    """Warranties expiring in > 30 days should generate 0 reminders."""
    today = date(2026, 8, 10)
    # Expiry in 100 days
    future_expiry = (today + timedelta(days=100)).isoformat()
    notifs = determine_eligible_notifications(
        expiry_date_str=future_expiry,
        target_date=today,
        product_name="MacBook Pro",
        warranty_type="AppleCare+"
    )
    assert len(notifs) == 0


def test_30_days_before_expiry():
    """Warranties expiring in exactly 30 days should generate 30D milestone reminder."""
    today = date(2026, 8, 10)
    expiry = (today + timedelta(days=30)).isoformat()
    notifs = determine_eligible_notifications(
        expiry_date_str=expiry,
        target_date=today,
        product_name="Sony TV",
        warranty_type="Comprehensive Warranty"
    )
    assert len(notifs) == 1
    assert notifs[0]["type"] == NotificationType.WARRANTY_EXPIRY_30D.value
    assert "Sony TV" in notifs[0]["message"]
    assert "30 days" in notifs[0]["message"]


def test_15_days_before_expiry():
    """Warranties expiring in 15 days generate 30D and 15D milestone reminders."""
    today = date(2026, 8, 10)
    expiry = (today + timedelta(days=15)).isoformat()
    notifs = determine_eligible_notifications(
        expiry_date_str=expiry,
        target_date=today,
        product_name="LG Refrigerator",
        warranty_type="Compressor Warranty"
    )
    types = [n["type"] for n in notifs]
    assert NotificationType.WARRANTY_EXPIRY_30D.value in types
    assert NotificationType.WARRANTY_EXPIRY_15D.value in types
    assert NotificationType.WARRANTY_EXPIRY_7D.value not in types


def test_7_days_and_1_day_before_expiry():
    """Warranties expiring in 7 days or 1 day generate appropriate reminders."""
    today = date(2026, 8, 10)
    
    # 7 days
    expiry_7d = (today + timedelta(days=7)).isoformat()
    notifs_7d = determine_eligible_notifications(expiry_7d, target_date=today)
    types_7d = [n["type"] for n in notifs_7d]
    assert NotificationType.WARRANTY_EXPIRY_7D.value in types_7d
    assert NotificationType.WARRANTY_EXPIRY_1D.value not in types_7d

    # 1 day
    expiry_1d = (today + timedelta(days=1)).isoformat()
    notifs_1d = determine_eligible_notifications(expiry_1d, target_date=today)
    types_1d = [n["type"] for n in notifs_1d]
    assert NotificationType.WARRANTY_EXPIRY_1D.value in types_1d
    assert NotificationType.WARRANTY_EXPIRY_0D.value not in types_1d


def test_on_expiry_date():
    """Warranties expiring today (0 days) generate the 0D milestone reminder."""
    today = date(2026, 8, 10)
    expiry_0d = today.isoformat()
    notifs = determine_eligible_notifications(
        expiry_date_str=expiry_0d,
        target_date=today,
        product_name="Dyson Vacuum",
        warranty_type="Motor Warranty"
    )
    types = [n["type"] for n in notifs]
    assert NotificationType.WARRANTY_EXPIRY_0D.value in types


def test_already_expired_warranty():
    """Warranties that are already expired generate a single EXPIRY_0D status alert without backlog spam."""
    today = date(2026, 8, 10)
    expired_date = (today - timedelta(days=45)).isoformat()
    notifs = determine_eligible_notifications(
        expiry_date_str=expired_date,
        target_date=today,
        product_name="Old Toaster",
        warranty_type="Seller Warranty"
    )
    assert len(notifs) == 1
    assert notifs[0]["type"] == NotificationType.WARRANTY_EXPIRY_0D.value
    assert "expired on" in notifs[0]["message"]


def test_same_product_multiple_warranties():
    """Same product with multiple warranty components generates independent reminders."""
    today = date(2026, 8, 10)
    
    # Component 1: Comprehensive (expires in 15 days)
    comp_notifs = determine_eligible_notifications(
        expiry_date_str=(today + timedelta(days=15)).isoformat(),
        target_date=today,
        product_name="Samsung Neo QLED",
        warranty_type="Comprehensive Warranty"
    )
    
    # Component 2: Panel (expires in 5 years / 1825 days)
    panel_notifs = determine_eligible_notifications(
        expiry_date_str=(today + timedelta(days=1825)).isoformat(),
        target_date=today,
        product_name="Samsung Neo QLED",
        warranty_type="Panel Warranty"
    )

    assert len(comp_notifs) >= 2  # 30D and 15D
    assert len(panel_notifs) == 0  # 0 because 5 years away
    assert "Comprehensive Warranty" in comp_notifs[0]["message"]
