import pytest
from datetime import datetime, timezone, date
from app.schemas.timeline import TimelineEvent, TimelineEventCreate
from app.services.timeline_service import EVENT_SORT_ORDER


def test_timeline_event_model():
    event = TimelineEvent(
        id="test-1",
        productId="prod-123",
        eventType="PURCHASE",
        title="Product Purchased",
        description="Purchased Apple iPhone 15 Pro",
        date="2026-08-10",
        category="purchase",
        status="completed",
        icon="shopping-cart",
        metadata={"price": 134900.0, "seller": "Apple Store"}
    )
    assert event.productId == "prod-123"
    assert event.eventType == "PURCHASE"
    assert event.status == "completed"
    assert event.metadata["price"] == 134900.0


def test_timeline_chronological_sorting():
    events = [
        TimelineEvent(
            id="e3",
            productId="p1",
            eventType="WARRANTY_EXPIRY",
            title="Warranty Expiry",
            description="Coverage ends",
            date="2027-08-10",
            category="warranty"
        ),
        TimelineEvent(
            id="e1",
            productId="p1",
            eventType="PURCHASE",
            title="Product Purchased",
            description="Acquired",
            date="2026-08-10",
            category="purchase"
        ),
        TimelineEvent(
            id="e2",
            productId="p1",
            eventType="RETURN_WINDOW_END",
            title="Return Deadline",
            description="Return window ends",
            date="2026-08-24",
            category="return"
        )
    ]

    def sort_key(event: TimelineEvent):
        d = datetime.strptime(event.date[:10], "%Y-%m-%d").date()
        priority = EVENT_SORT_ORDER.get(event.eventType, 50)
        return (d, priority, event.title)

    sorted_events = sorted(events, key=sort_key)
    assert [e.id for e in sorted_events] == ["e1", "e2", "e3"]


def test_custom_lifecycle_event_create_model():
    create_dto = TimelineEventCreate(
        eventType="SERVICE",
        title="Annual Routine Cleaning & Maintenance",
        description="Cleaned condenser coils and refilled coolant.",
        date="2026-11-15",
        category="service",
        status="completed",
        icon="wrench",
        metadata={"technician": "Urban Company", "cost": 799.0}
    )
    assert create_dto.eventType == "SERVICE"
    assert create_dto.category == "service"
    assert create_dto.metadata["cost"] == 799.0
