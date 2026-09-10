from datetime import datetime
from typing import Optional, List, Dict, Any, Literal
from pydantic import BaseModel, Field

TimelineEventType = Literal[
    "PURCHASE",
    "REGISTRATION",
    "RETURN_WINDOW_START",
    "RETURN_WINDOW_END",
    "WARRANTY_START",
    "WARRANTY_EXPIRY",
    "DOCUMENT_ATTACHED",
    "NOTIFICATION_ALERT",
    "MAINTENANCE",
    "SERVICE",
    "REPAIR",
    "CUSTOM"
]

TimelineCategory = Literal[
    "purchase",
    "return",
    "warranty",
    "document",
    "alert",
    "service",
    "maintenance",
    "other"
]

TimelineStatus = Literal[
    "completed",
    "active",
    "upcoming",
    "critical",
    "info"
]


class TimelineEvent(BaseModel):
    id: str = Field(..., description="Unique deterministic or persistent ID for the timeline event")
    productId: str = Field(..., description="Associated product ID")
    eventType: str = Field(..., description="Type of lifecycle event")
    title: str = Field(..., description="Event title")
    description: str = Field(..., description="Detailed event description")
    date: str = Field(..., description="Event date in YYYY-MM-DD or ISO format")
    category: TimelineCategory = Field(default="other", description="Category for visual color theme")
    status: TimelineStatus = Field(default="completed", description="State of the milestone")
    icon: Optional[str] = Field(None, description="Icon identifier for frontend rendering")
    metadata: Optional[Dict[str, Any]] = Field(default_factory=dict, description="Arbitrary event metadata")
    createdAt: Optional[datetime] = None


class TimelineEventCreate(BaseModel):
    eventType: str = Field(..., description="e.g. SERVICE, MAINTENANCE, REPAIR, CUSTOM")
    title: str = Field(..., min_length=1, max_length=120, description="Title of the lifecycle event")
    description: str = Field(..., min_length=1, max_length=1000, description="Event notes or details")
    date: str = Field(..., description="Date of the event (YYYY-MM-DD)")
    category: TimelineCategory = Field(default="service", description="Category for visual styling")
    status: TimelineStatus = Field(default="completed", description="Status of the event")
    icon: Optional[str] = Field(default="wrench", description="Icon name")
    metadata: Optional[Dict[str, Any]] = Field(default_factory=dict)


class TimelineResponse(BaseModel):
    productId: str
    productName: str
    events: List[TimelineEvent]
    totalEvents: int
