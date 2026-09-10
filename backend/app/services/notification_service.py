import logging
from datetime import datetime, date, timezone
from typing import List, Optional, Dict, Any
from bson import ObjectId
from pymongo import ASCENDING, DESCENDING

from app.core.database import db_manager
from app.schemas.notification import (
    NotificationType,
    NotificationResponse,
    NotificationCheckResult
)

logger = logging.getLogger("ownit.notifications")

MILESTONE_THRESHOLDS = [
    (30, NotificationType.WARRANTY_EXPIRY_30D, "expires in 30 days"),
    (15, NotificationType.WARRANTY_EXPIRY_15D, "expires in 15 days"),
    (7, NotificationType.WARRANTY_EXPIRY_7D, "expires in 7 days (urgent)"),
    (1, NotificationType.WARRANTY_EXPIRY_1D, "expires tomorrow"),
    (0, NotificationType.WARRANTY_EXPIRY_0D, "has expired today")
]


def determine_eligible_notifications(
    expiry_date_str: str,
    target_date: Optional[date] = None,
    product_name: str = "Product",
    warranty_type: str = "Warranty"
) -> List[Dict[str, Any]]:
    """
    Pure business logic function to evaluate which notification milestone(s)
    are eligible for a given warranty expiry date relative to target_date.
    
    Returns a list of dicts: [{'type': str, 'message': str, 'scheduledDate': str}]
    """
    if not expiry_date_str:
        return []

    try:
        expiry_date = datetime.strptime(expiry_date_str, "%Y-%m-%d").date()
    except ValueError:
        return []

    if target_date is None:
        target_date = datetime.now(timezone.utc).date()

    days_remaining = (expiry_date - target_date).days

    # Future warranty beyond 30 days -> no notification yet
    if days_remaining > 30:
        return []

    # If warranty is already long expired (days_remaining < 0),
    # only generate the EXPIRY_0D notification to prevent spamming 30D/15D/7D backlog.
    if days_remaining < 0:
        return [
            {
                "type": NotificationType.WARRANTY_EXPIRY_0D.value,
                "message": f"Coverage Ended: Your {warranty_type} for {product_name} expired on {expiry_date_str}.",
                "scheduledDate": target_date.isoformat()
            }
        ]

    eligible = []
    # If currently at exact or within milestone days, include all milestones reached
    for threshold_days, notif_type, desc in MILESTONE_THRESHOLDS:
        if days_remaining <= threshold_days:
            if threshold_days == 0:
                msg = f"Coverage Alert: Your {warranty_type} for {product_name} expires today ({expiry_date_str})."
            elif threshold_days == 1:
                msg = f"Final Notice: Your {warranty_type} for {product_name} expires tomorrow ({expiry_date_str})."
            elif threshold_days == 7:
                msg = f"Urgent: Your {warranty_type} for {product_name} expires in {days_remaining} days ({expiry_date_str}). Action may be needed."
            else:
                msg = f"Reminder: Your {warranty_type} for {product_name} expires in {days_remaining} days ({expiry_date_str})."

            eligible.append({
                "type": notif_type.value,
                "message": msg,
                "scheduledDate": target_date.isoformat()
            })

    return eligible


class NotificationService:
    @property
    def collection(self):
        return db_manager.get_collection("notifications")

    @property
    def warranties_collection(self):
        return db_manager.get_collection("warranties")

    @property
    def products_collection(self):
        return db_manager.get_collection("products")

    async def ensure_indexes(self):
        """
        Creates compound unique index on (userId, warrantyId, type)
        to prevent any duplicate notifications.
        Also indexes createdAt and isRead for high-performance listing and badges.
        """
        try:
            col = self.collection
            # Compound unique index prevents duplicate notification records
            await col.create_index(
                [("userId", ASCENDING), ("warrantyId", ASCENDING), ("type", ASCENDING)],
                unique=True,
                name="idx_unique_user_warranty_notification"
            )
            # Query indexes
            await col.create_index([("userId", ASCENDING), ("createdAt", DESCENDING)], name="idx_user_created_at")
            await col.create_index([("userId", ASCENDING), ("isRead", ASCENDING)], name="idx_user_unread")
            logger.info("MongoDB indexes for notifications collection verified.")
        except Exception as e:
            logger.warning(f"Failed to create notification indexes: {e}")

    async def evaluate_warranty_reminders(
        self,
        user_id: Optional[str] = None,
        target_date: Optional[date] = None
    ) -> NotificationCheckResult:
        """
        Scans active/expiring warranties, computes milestone triggers,
        and safely inserts new notifications without duplicates.
        """
        if target_date is None:
            target_date = datetime.now(timezone.utc).date()

        query: Dict[str, Any] = {}
        if user_id:
            query["userId"] = user_id

        cursor = self.warranties_collection.find(query)
        warranties = await cursor.to_list(length=10000)

        # Build product names cache
        product_ids = [w.get("productId") for w in warranties if w.get("productId")]
        product_names_map: Dict[str, str] = {}
        if product_ids:
            prod_cursor = self.products_collection.find({"_id": {"$in": [ObjectId(pid) for pid in product_ids if ObjectId.is_valid(pid)]}})
            async for prod in prod_cursor:
                product_names_map[str(prod["_id"])] = prod.get("name", "Product")

        created_count = 0

        for w in warranties:
            w_id = str(w["_id"])
            w_user_id = w.get("userId")
            w_prod_id = w.get("productId")
            w_type = w.get("type", "Warranty")
            w_expiry = w.get("expiryDate")
            prod_name = product_names_map.get(w_prod_id, "Product")

            if not w_expiry or not w_user_id:
                continue

            eligible_notifs = determine_eligible_notifications(
                expiry_date_str=w_expiry,
                target_date=target_date,
                product_name=prod_name,
                warranty_type=w_type
            )

            for notif_item in eligible_notifs:
                # Check if notification already exists for this (userId, warrantyId, type)
                existing = await self.collection.find_one({
                    "userId": w_user_id,
                    "warrantyId": w_id,
                    "type": notif_item["type"]
                })

                if existing is None:
                    try:
                        doc = {
                            "userId": w_user_id,
                            "productId": w_prod_id,
                            "warrantyId": w_id,
                            "type": notif_item["type"],
                            "message": notif_item["message"],
                            "scheduledDate": notif_item["scheduledDate"],
                            "isRead": False,
                            "createdAt": datetime.now(timezone.utc)
                        }
                        await self.collection.insert_one(doc)
                        created_count += 1
                        logger.info(f"Created {notif_item['type']} notification for warranty {w_id} ({prod_name})")
                    except Exception as ex:
                        # Duplicate key collision safe handling
                        logger.debug(f"Notification insert skipped or duplicate: {ex}")

        return NotificationCheckResult(
            evaluatedWarranties=len(warranties),
            newNotificationsCreated=created_count,
            evaluatedDate=target_date.isoformat()
        )

    async def get_user_notifications(
        self,
        user_id: str,
        unread_only: bool = False,
        limit: int = 50
    ) -> List[NotificationResponse]:
        """
        Retrieves user notifications sorted by creation date descending.
        """
        query: Dict[str, Any] = {"userId": user_id}
        if unread_only:
            query["isRead"] = False

        cursor = self.collection.find(query).sort("createdAt", DESCENDING).limit(limit)
        docs = await cursor.to_list(length=limit)

        # Hydrate with product names and warranty types for rich UI
        results: List[NotificationResponse] = []
        for doc in docs:
            results.append(
                NotificationResponse(
                    id=str(doc["_id"]),
                    userId=doc["userId"],
                    productId=doc.get("productId"),
                    warrantyId=doc.get("warrantyId"),
                    type=doc["type"],
                    message=doc["message"],
                    scheduledDate=doc.get("scheduledDate", ""),
                    isRead=doc.get("isRead", False),
                    createdAt=doc.get("createdAt", datetime.now(timezone.utc))
                )
            )
        return results

    async def get_unread_count(self, user_id: str) -> int:
        """
        Returns the count of unread notifications for the user.
        """
        return await self.collection.count_documents({"userId": user_id, "isRead": False})

    async def mark_as_read(self, user_id: str, notification_id: str) -> Optional[NotificationResponse]:
        """
        Marks a specific notification as read.
        """
        if not ObjectId.is_valid(notification_id):
            return None

        result = await self.collection.find_one_and_update(
            {"_id": ObjectId(notification_id), "userId": user_id},
            {"$set": {"isRead": True}},
            return_document=True
        )

        if not result:
            return None

        return NotificationResponse(
            id=str(result["_id"]),
            userId=result["userId"],
            productId=result.get("productId"),
            warrantyId=result.get("warrantyId"),
            type=result["type"],
            message=result["message"],
            scheduledDate=result.get("scheduledDate", ""),
            isRead=result.get("isRead", True),
            createdAt=result.get("createdAt", datetime.now(timezone.utc))
        )

    async def mark_all_as_read(self, user_id: str) -> int:
        """
        Marks all unread notifications for a user as read.
        Returns the number of updated notifications.
        """
        result = await self.collection.update_many(
            {"userId": user_id, "isRead": False},
            {"$set": {"isRead": True}}
        )
        return result.modified_count

    async def delete_notification(self, user_id: str, notification_id: str) -> bool:
        """
        Deletes a specific notification belonging to the user.
        """
        if not ObjectId.is_valid(notification_id):
            return False

        result = await self.collection.delete_one({"_id": ObjectId(notification_id), "userId": user_id})
        return result.deleted_count > 0


notification_service = NotificationService()
