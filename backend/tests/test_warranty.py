import pytest
from datetime import datetime, timezone, timedelta, date
from app.services.warranty_service import (
    calculate_warranty_status,
    calculate_expiry_date
)
from app.schemas.warranty import WarrantyCreate, WarrantyUpdate


def test_calculate_expiry_date_from_duration():
    # 1. 1 Year default
    start = "2026-08-10"
    exp_1y = calculate_expiry_date(start, "1 Year")
    assert exp_1y == "2027-08-10"

    # 2. 2 Years
    exp_2y = calculate_expiry_date(start, "2 Years")
    assert exp_2y == "2028-08-10"

    # 3. 24 Months
    exp_24m = calculate_expiry_date(start, "24 Months")
    assert exp_24m == "2028-08-10"

    # 4. 5 Years (e.g. Panel Warranty)
    exp_5y = calculate_expiry_date(start, "5 Years")
    assert exp_5y == "2031-08-10"

    # 5. 90 Days
    exp_90d = calculate_expiry_date(start, "90 Days")
    exp_dt = datetime.strptime(start, "%Y-%m-%d").date() + timedelta(days=90)
    assert exp_90d == exp_dt.strftime("%Y-%m-%d")


def test_calculate_warranty_status():
    today = datetime.now(timezone.utc).date()

    # 1. Active: Expiry 100 days in future
    future_date = (today + timedelta(days=100)).strftime("%Y-%m-%d")
    status, days, color = calculate_warranty_status(future_date)
    assert status == "Active"
    assert days == 100
    assert color == "green"

    # 2. Expiring Soon: Expiry 15 days in future (<= 30 days)
    soon_date = (today + timedelta(days=15)).strftime("%Y-%m-%d")
    status, days, color = calculate_warranty_status(soon_date)
    assert status == "Expiring Soon"
    assert days == 15
    assert color == "amber"

    # 3. Expiring Soon boundary: Expiry today (0 days)
    today_date = today.strftime("%Y-%m-%d")
    status, days, color = calculate_warranty_status(today_date)
    assert status == "Expiring Soon"
    assert days == 0
    assert color == "amber"

    # 4. Expired: Expiry 10 days in past (< 0 days)
    past_date = (today - timedelta(days=10)).strftime("%Y-%m-%d")
    status, days, color = calculate_warranty_status(past_date)
    assert status == "Expired"
    assert days == -10
    assert color == "red"


def test_multiple_warranty_components_model():
    """
    Verifies user's exact example:
    Comprehensive Warranty: Start 10 Aug 2026, Expiry 10 Aug 2028
    Panel Warranty: Start 10 Aug 2026, Expiry 10 Aug 2031
    """
    comp = WarrantyCreate(
        productId="507f1f77bcf86cd799439011",
        type="Comprehensive Warranty",
        provider="Samsung",
        duration="2 Years",
        startDate="2026-08-10",
        expiryDate="2028-08-10",
        benefits="Comprehensive coverage for all internal circuits and labor",
        claimProcedure="Call Samsung toll-free customer support"
    )
    assert comp.type == "Comprehensive Warranty"
    assert comp.startDate == "2026-08-10"
    assert comp.expiryDate == "2028-08-10"

    panel = WarrantyCreate(
        productId="507f1f77bcf86cd799439011",
        type="Panel Warranty",
        provider="Samsung",
        duration="5 Years",
        startDate="2026-08-10",
        expiryDate="2031-08-10",
        benefits="Direct replacement for OLED/LED panel defects",
        claimProcedure="Call Samsung toll-free customer support"
    )
    assert panel.type == "Panel Warranty"
    assert panel.startDate == "2026-08-10"
    assert panel.expiryDate == "2031-08-10"
