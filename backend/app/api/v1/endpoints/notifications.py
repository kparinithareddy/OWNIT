from typing import List, Optional
from fastapi import APIRouter, Depends, HTTPException, status, Query

from app.api.v1.endpoints.auth import get_current_user
from app.schemas.user import UserResponse
from app.schemas.notification import (
    NotificationResponse,
    NotificationUnreadCountResponse,
    NotificationCheckResult
)
from app.services.notification_service import notification_service

router = APIRouter()


@router.get("/", response_model=List[NotificationResponse])
async def list_notifications(
    unread_only: bool = Query(False, description="Filter only unread notifications"),
    limit: int = Query(50, ge=1, le=100),
    current_user: UserResponse = Depends(get_current_user)
):
    """
    List user notifications sorted by most recent first.
    """
    return await notification_service.get_user_notifications(
        user_id=current_user.id,
        unread_only=unread_only,
        limit=limit
    )


@router.get("/unread-count", response_model=NotificationUnreadCountResponse)
async def get_unread_count(
    current_user: UserResponse = Depends(get_current_user)
):
    """
    Get the total count of unread notifications for the badge counter.
    """
    count = await notification_service.get_unread_count(user_id=current_user.id)
    return NotificationUnreadCountResponse(unreadCount=count)


@router.put("/{notification_id}/read", response_model=NotificationResponse)
async def mark_notification_read(
    notification_id: str,
    current_user: UserResponse = Depends(get_current_user)
):
    """
    Mark a single notification as read.
    """
    updated = await notification_service.mark_as_read(
        user_id=current_user.id,
        notification_id=notification_id
    )
    if not updated:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Notification not found or access denied"
        )
    return updated


@router.post("/mark-all-read", response_model=dict)
async def mark_all_notifications_read(
    current_user: UserResponse = Depends(get_current_user)
):
    """
    Mark all unread notifications as read for current user.
    """
    modified = await notification_service.mark_all_as_read(user_id=current_user.id)
    return {"status": "ok", "modifiedCount": modified}


@router.post("/trigger-check", response_model=NotificationCheckResult)
async def trigger_notification_check(
    current_user: UserResponse = Depends(get_current_user)
):
    """
    Manually trigger an evaluation of warranty reminders for the current user.
    """
    result = await notification_service.evaluate_warranty_reminders(user_id=current_user.id)
    return result


@router.delete("/{notification_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_notification(
    notification_id: str,
    current_user: UserResponse = Depends(get_current_user)
):
    """
    Delete a notification.
    """
    deleted = await notification_service.delete_notification(
        user_id=current_user.id,
        notification_id=notification_id
    )
    if not deleted:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Notification not found or access denied"
        )
    return None
