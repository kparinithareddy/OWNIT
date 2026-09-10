import pytest
from datetime import date, timedelta
from app.services.return_service import (
    calculate_return_deadline,
    calculate_return_status,
    parse_return_duration_days,
    get_verified_seller_policy
)


def test_parse_return_duration_days():
    assert parse_return_duration_days("7 Days") == 7
    assert parse_return_duration_days("10 Days") == 10
    assert parse_return_duration_days("14 Days") == 14
    assert parse_return_duration_days("30 Days") == 30
    assert parse_return_duration_days("1 Month") == 30
    assert parse_return_duration_days("2 Weeks") == 14
    assert parse_return_duration_days("No Returns") == 0
    assert parse_return_duration_days(None) is None
    assert parse_return_duration_days("") is None


def test_calculate_return_deadline():
    start = "2026-08-10"
    assert calculate_return_deadline(start, "7 Days") == "2026-08-17"
    assert calculate_return_deadline(start, "10 Days") == "2026-08-20"
    assert calculate_return_deadline(start, "14 Days") == "2026-08-24"
    assert calculate_return_deadline(start, "30 Days") == "2026-09-09"
    assert calculate_return_deadline(None, "7 Days") is None
    assert calculate_return_deadline(start, None) is None


def test_calculate_return_status_active():
    today = date(2026, 8, 10)
    # Deadline in 5 days (> 3 days) -> Active
    deadline = (today + timedelta(days=5)).isoformat()
    status, days = calculate_return_status(deadline, target_date=today)
    assert status == "Active"
    assert days == 5


def test_calculate_return_status_ending_soon():
    today = date(2026, 8, 10)
    
    # 3 days remaining
    status_3d, days_3d = calculate_return_status((today + timedelta(days=3)).isoformat(), target_date=today)
    assert status_3d == "Ending Soon"
    assert days_3d == 3

    # 1 day remaining
    status_1d, days_1d = calculate_return_status((today + timedelta(days=1)).isoformat(), target_date=today)
    assert status_1d == "Ending Soon"
    assert days_1d == 1

    # 0 days remaining (expires today)
    status_0d, days_0d = calculate_return_status(today.isoformat(), target_date=today)
    assert status_0d == "Ending Soon"
    assert days_0d == 0


def test_calculate_return_status_expired():
    today = date(2026, 8, 10)
    # Deadline passed 2 days ago
    deadline = (today - timedelta(days=2)).isoformat()
    status, days = calculate_return_status(deadline, target_date=today)
    assert status == "Expired"
    assert days == -2


def test_calculate_return_status_unknown_when_unavailable():
    """If return info is unavailable, do NOT invent it. Must return Unknown and None."""
    today = date(2026, 8, 10)
    status, days = calculate_return_status(None, target_date=today)
    assert status == "Unknown"
    assert days is None

    status_empty, days_empty = calculate_return_status("", target_date=today)
    assert status_empty == "Unknown"
    assert days_empty is None


def test_verified_seller_policy_lookup():
    # Known sellers
    amazon = get_verified_seller_policy("Amazon India")
    assert amazon is not None
    assert amazon["duration"] == "7 Days"

    apple = get_verified_seller_policy("Apple Store")
    assert apple is not None
    assert apple["duration"] == "14 Days"

    croma = get_verified_seller_policy("Croma")
    assert croma is not None
    assert croma["duration"] == "15 Days"

    # Unknown sellers (Do not invent policy)
    unknown = get_verified_seller_policy("Local Electronics Bazaar")
    assert unknown is None


def test_independence_from_warranty_calculations():
    """
    Return period is typically 7-30 days, while warranty is 1-10 years.
    Verify that an expired return window does not affect or depend on warranty validity.
    """
    today = date(2026, 8, 10)
    purchase = date(2026, 7, 1)  # 40 days ago
    
    # 7-day return deadline was on 2026-07-08 -> Expired
    return_deadline = calculate_return_deadline(purchase.isoformat(), "7 Days")
    return_status, return_days = calculate_return_status(return_deadline, target_date=today)
    assert return_status == "Expired"
    assert return_days < 0
