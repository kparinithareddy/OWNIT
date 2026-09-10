from datetime import datetime
from enum import Enum
from typing import Optional, List
from pydantic import BaseModel, Field


class NotificationType(str, Enum):
    WARRANTY_EXPIRY_30D = "WARRANTY_EXPIRY_30D"
    WARRANTY_EXPIRY_15D = "WARRANTY_EXPIRY_15D"
    WARRANTY_EXPIRY_7D = "WARRANTY_EXPIRY_7D"
    WARRANTY_EXPIRY_1D = "WARRANTY_EXPIRY_1D"
    WARRANTY_EXPIRY_0D = "WARRANTY_EXPIRY_0D"
    GENERAL = "GENERAL"


class NotificationBase(BaseModel):
    userId: str = Field(..., description="ID of user receiving the notification")
    productId: Optional[str] = Field(None, description="Associated product ID")
    warrantyId: Optional[str] = Field(None, description="Associated warranty ID")
    type: str = Field(..., description="Notification category/milestone type")
    message: str = Field(..., description="User-facing notification text")
    scheduledDate: str = Field(..., description="Date scheduled/evaluated for (YYYY-MM-DD)")
    isRead: bool = Field(default=False, description="Whether user has read this notification")


class NotificationCreate(NotificationBase):
    pass


class NotificationResponse(BaseModel):
    id: str
    userId: str
    productId: Optional[str] = None
    warrantyId: Optional[str] = None
    type: str
    message: str
    scheduledDate: str
    isRead: bool = False
    createdAt: datetime
    productName: Optional[str] = None
    warrantyType: Optional[str] = None

    class Config:
        populate_by_name = True


class NotificationUnreadCountResponse(BaseModel):
    unreadCount: int


class NotificationCheckResult(BaseModel):
    evaluatedWarranties: int
    newNotificationsCreated: int
    evaluatedDate: str
