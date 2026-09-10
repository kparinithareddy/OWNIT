from datetime import datetime, date, timedelta, timezone
from typing import Optional, Tuple, Dict, Any

# Verified seller return policies dictionary
# Do NOT assume every seller has the same return policy.
# Only known verified sellers are mapped, and user can always override.
VERIFIED_SELLER_POLICIES = {
    "amazon": {
        "duration": "7 Days",
        "durationDays": 7,
        "source": "Amazon India Standard Replacement Policy"
    },
    "amazon india": {
        "duration": "7 Days",
        "durationDays": 7,
        "source": "Amazon India Standard Replacement Policy"
    },
    "flipkart": {
        "duration": "7 Days",
        "durationDays": 7,
        "source": "Flipkart 7-Day Replacement Policy"
    },
    "apple": {
        "duration": "14 Days",
        "durationDays": 14,
        "source": "Apple Store 14-Day Return Policy"
    },
    "apple store": {
        "duration": "14 Days",
        "durationDays": 14,
        "source": "Apple Store 14-Day Return Policy"
    },
    "croma": {
        "duration": "15 Days",
        "durationDays": 15,
        "source": "Croma 15-Day Exchange/Return Policy"
    },
    "reliance digital": {
        "duration": "7 Days",
        "durationDays": 7,
        "source": "Reliance Digital 7-Day Replacement Policy"
    },
    "samsung": {
        "duration": "14 Days",
        "durationDays": 14,
        "source": "Samsung Official Shop 14-Day Return Policy"
    },
    "samsung shop": {
        "duration": "14 Days",
        "durationDays": 14,
        "source": "Samsung Official Shop 14-Day Return Policy"
    }
}


def get_verified_seller_policy(seller_name: Optional[str]) -> Optional[Dict[str, Any]]:
    """
    Looks up verified seller return policy if available.
    Returns None if seller is unknown or blank (do NOT invent policy).
    """
    if not seller_name:
        return None
    normalized = seller_name.strip().lower()
    return VERIFIED_SELLER_POLICIES.get(normalized)


def parse_return_duration_days(duration_str: Optional[str]) -> Optional[int]:
    """
    Parses a duration string (e.g. '7 Days', '10 Days', '14 Days', '30 Days', '1 Month')
    into integer days. Returns None if unknown or 'No Returns'.
    """
    if not duration_str:
        return None
    dur = duration_str.strip().lower()
    if "no return" in dur or "none" in dur or dur == "0" or dur == "0 days":
        return 0

    import re
    # Match days
    day_match = re.search(r"(\d+)\s*(?:day|d)", dur)
    if day_match:
        return int(day_match.group(1))

    # Match weeks
    week_match = re.search(r"(\d+)\s*(?:week|wk|w)", dur)
    if week_match:
        return int(week_match.group(1)) * 7

    # Match months
    month_match = re.search(r"(\d+)\s*(?:month|mo|m)", dur)
    if month_match:
        return int(month_match.group(1)) * 30

    return None


def calculate_return_deadline(
    start_date_str: Optional[str],
    duration_str: Optional[str]
) -> Optional[str]:
    """
    Calculates return deadline (YYYY-MM-DD) from start date and duration.
    Returns None if inputs are insufficient.
    """
    if not start_date_str or not duration_str:
        return None

    try:
        start_date = datetime.strptime(start_date_str.strip(), "%Y-%m-%d").date()
    except ValueError:
        return None

    days = parse_return_duration_days(duration_str)
    if days is None:
        return None

    deadline = start_date + timedelta(days=days)
    return deadline.isoformat()


def calculate_return_status(
    deadline_str: Optional[str],
    target_date: Optional[date] = None
) -> Tuple[str, Optional[int]]:
    """
    Calculates return status and days remaining.
    
    Statuses:
    - Active: > 3 days remaining
    - Ending Soon: 0 <= days remaining <= 3
    - Expired: < 0 days remaining
    - Unknown: When deadline is missing or unrecorded (do NOT invent info).
    
    Returns (status: str, days_remaining: Optional[int])
    """
    if not deadline_str:
        return "Unknown", None

    try:
        deadline = datetime.strptime(deadline_str.strip(), "%Y-%m-%d").date()
    except ValueError:
        return "Unknown", None

    if target_date is None:
        target_date = datetime.now(timezone.utc).date()

    days_remaining = (deadline - target_date).days

    if days_remaining > 3:
        return "Active", days_remaining
    elif 0 <= days_remaining <= 3:
        return "Ending Soon", days_remaining
    else:
        return "Expired", days_remaining
