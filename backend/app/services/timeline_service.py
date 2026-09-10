import logging
from datetime import datetime, timezone, date
from typing import List, Optional, Dict, Any
from bson import ObjectId
from pymongo import ASCENDING, DESCENDING

from app.core.database import db_manager
from app.core.exceptions import NotFoundException
from app.schemas.timeline import (
    TimelineEvent,
    TimelineEventCreate,
    TimelineResponse
)
from app.services.product_service import product_service
from app.services.warranty_service import warranty_service

logger = logging.getLogger("ownit.services.timeline")

EVENT_SORT_ORDER = {
    "PURCHASE": 10,
    "REGISTRATION": 20,
    "DOCUMENT_ATTACHED": 30,
    "RETURN_WINDOW_START": 40,
    "WARRANTY_START": 50,
    "MAINTENANCE": 60,
    "SERVICE": 70,
    "REPAIR": 75,
    "CUSTOM": 80,
    "NOTIFICATION_ALERT": 85,
    "RETURN_WINDOW_END": 90,
    "WARRANTY_EXPIRY": 100
}


class TimelineService:
    @property
    def events_collection(self):
        return db_manager.get_collection("lifecycle_events")

    @property
    def documents_collection(self):
        return db_manager.get_collection("documents")

    @property
    def notifications_collection(self):
        return db_manager.get_collection("notifications")

    @property
    def maintenance_collection(self):
        return db_manager.get_collection("maintenance_records")


    async def ensure_indexes(self):
        try:
            col = self.events_collection
            await col.create_index(
                [("productId", ASCENDING), ("userId", ASCENDING), ("date", ASCENDING)],
                name="idx_timeline_product_user_date"
            )
            logger.info("Lifecycle events indexes ensured in MongoDB.")
        except Exception as e:
            logger.warning(f"Could not create lifecycle events indexes: {e}")

    async def get_product_timeline(self, product_id: str, user_id: str) -> TimelineResponse:
        """
        Derives and aggregates all authentic lifecycle events from actual database records
        (Product details, Return deadlines, Warranties, Attached Documents, Notifications, and Service logs).
        Returns them in sorted chronological order.
        """
        # 1. Fetch and verify product ownership
        product = await product_service.get_product_by_id(product_id, user_id)

        events: List[TimelineEvent] = []
        today = datetime.now(timezone.utc).date()

        # 2. Derive Product Purchase Event
        if product.purchaseDate:
            seller_str = f" from {product.seller}" if product.seller else ""
            events.append(
                TimelineEvent(
                    id=f"purchase-{product.id}",
                    productId=product.id,
                    eventType="PURCHASE",
                    title="Product Purchased",
                    description=f"Purchased {product.brand} {product.name}{seller_str} for ₹{product.price:,.2f}.",
                    date=product.purchaseDate,
                    category="purchase",
                    status="completed",
                    icon="shopping-cart",
                    metadata={
                        "price": product.price,
                        "seller": product.seller,
                        "model": product.model,
                        "quantity": product.quantity
                    }
                )
            )

        # 3. Derive Return & Replacement Window Events
        if product.returnDuration and product.returnDuration != "None" and product.returnDuration != "No Returns":
            start_date = product.returnStartDate or product.purchaseDate
            if start_date:
                events.append(
                    TimelineEvent(
                        id=f"return-start-{product.id}",
                        productId=product.id,
                        eventType="RETURN_WINDOW_START",
                        title="Return Window Opened",
                        description=f"{product.returnDuration} return / replacement period started.",
                        date=start_date,
                        category="return",
                        status="completed",
                        icon="rotate-ccw",
                        metadata={
                            "duration": product.returnDuration,
                            "source": product.returnPolicySource
                        }
                    )
                )

            if product.returnDeadline:
                days = product.returnDaysRemaining
                ret_status = "completed" if (days is not None and days < 0) else ("critical" if (days is not None and days <= 3) else "active")
                events.append(
                    TimelineEvent(
                        id=f"return-end-{product.id}",
                        productId=product.id,
                        eventType="RETURN_WINDOW_END",
                        title="Return Window Deadline",
                        description=f"Last day for return/exchange under {product.returnPolicySource or 'seller policy'}.",
                        date=product.returnDeadline,
                        category="return",
                        status=ret_status,
                        icon="rotate-ccw",
                        metadata={
                            "deadline": product.returnDeadline,
                            "daysRemaining": days,
                            "returnStatus": product.returnStatus
                        }
                    )
                )

        # 4. Derive Warranty Component Events
        warranties = await warranty_service.get_warranties_by_product(product_id, user_id)
        for w in warranties:
            # Warranty Start
            if w.startDate:
                events.append(
                    TimelineEvent(
                        id=f"warranty-start-{w.id}",
                        productId=product.id,
                        eventType="WARRANTY_START",
                        title=f"{w.type} Coverage Started",
                        description=f"Protection activated by {w.provider} for {w.duration}.",
                        date=w.startDate,
                        category="warranty",
                        status="completed",
                        icon="shield-check",
                        metadata={
                            "warrantyId": w.id,
                            "provider": w.provider,
                            "duration": w.duration,
                            "type": w.type
                        }
                    )
                )

            # Warranty Expiry
            if w.expiryDate:
                w_status = "completed" if w.daysRemaining < 0 else ("critical" if w.daysRemaining <= 30 else "upcoming")
                events.append(
                    TimelineEvent(
                        id=f"warranty-expiry-{w.id}",
                        productId=product.id,
                        eventType="WARRANTY_EXPIRY",
                        title=f"{w.type} Expiry Date",
                        description=f"Coverage concludes on {w.expiryDate} ({w.daysRemaining} days remaining).",
                        date=w.expiryDate,
                        category="warranty",
                        status=w_status,
                        icon="shield-alert",
                        metadata={
                            "warrantyId": w.id,
                            "expiryDate": w.expiryDate,
                            "daysRemaining": w.daysRemaining,
                            "status": w.status
                        }
                    )
                )

        # 5. Derive Attached Document Events
        doc_cursor = self.documents_collection.find({"productId": product_id, "userId": user_id})
        async for doc in doc_cursor:
            doc_date = doc.get("uploadedAt", datetime.now(timezone.utc)).strftime("%Y-%m-%d")
            events.append(
                TimelineEvent(
                    id=f"doc-{doc['_id']}",
                    productId=product.id,
                    eventType="DOCUMENT_ATTACHED",
                    title=f"{doc.get('documentType', 'Document')} Attached",
                    description=f"Uploaded {doc.get('originalFilename', 'file')} to record storage.",
                    date=doc_date,
                    category="document",
                    status="completed",
                    icon="file-text",
                    metadata={
                        "documentId": str(doc["_id"]),
                        "filename": doc.get("originalFilename"),
                        "documentType": doc.get("documentType"),
                        "fileSize": doc.get("fileSize")
                    }
                )
            )

        # 6. Derive In-App Alerts & Notifications
        notif_cursor = self.notifications_collection.find({"productId": product_id, "userId": user_id})
        async for notif in notif_cursor:
            notif_date = notif.get("scheduledDate") or notif.get("createdAt", datetime.now(timezone.utc)).strftime("%Y-%m-%d")
            events.append(
                TimelineEvent(
                    id=f"notif-{notif['_id']}",
                    productId=product.id,
                    eventType="NOTIFICATION_ALERT",
                    title="Warranty Milestone Alert",
                    description=notif.get("message", "Expiration reminder triggered."),
                    date=notif_date,
                    category="alert",
                    status="completed" if notif.get("isRead") else "active",
                    icon="bell",
                    metadata={
                        "notificationId": str(notif["_id"]),
                        "type": notif.get("type"),
                        "isRead": notif.get("isRead")
                    }
                )
            )

        # 7. Include Dedicated Product Maintenance Records
        maint_cursor = self.maintenance_collection.find({"productId": product_id, "userId": user_id})
        async for m_rec in maint_cursor:
            m_status = "completed" if m_rec.get("status") == "Completed" else ("critical" if m_rec.get("status") == "Overdue" else "active")
            events.append(
                TimelineEvent(
                    id=f"maint-{m_rec['_id']}",
                    productId=product.id,
                    eventType="MAINTENANCE",
                    title=m_rec.get("title", "Maintenance Action"),
                    description=m_rec.get("description") or f"{m_rec.get('type', 'Service')} performed on asset.",
                    date=m_rec.get("date", ""),
                    category="maintenance",
                    status=m_status,
                    icon="wrench",
                    metadata={
                        "maintenanceId": str(m_rec["_id"]),
                        "type": m_rec.get("type"),
                        "cost": m_rec.get("cost"),
                        "provider": m_rec.get("serviceProvider"),
                        "status": m_rec.get("status"),
                        "documentId": m_rec.get("documentId"),
                        "nextDueDate": m_rec.get("nextDueDate")
                    },
                    createdAt=m_rec.get("createdAt")
                )
            )

        # 8. Include Custom Service / Maintenance / Repair Events from lifecycle_events
        custom_cursor = self.events_collection.find({"productId": product_id, "userId": user_id})
        async for c_event in custom_cursor:
            events.append(
                TimelineEvent(
                    id=str(c_event["_id"]),
                    productId=product.id,
                    eventType=c_event.get("eventType", "SERVICE"),
                    title=c_event.get("title", "Service Event"),
                    description=c_event.get("description", ""),
                    date=c_event.get("date", ""),
                    category=c_event.get("category", "service"),
                    status=c_event.get("status", "completed"),
                    icon=c_event.get("icon", "wrench"),
                    metadata=c_event.get("metadata", {}),
                    createdAt=c_event.get("createdAt")
                )
            )

        # 9. Sort chronologically by date ascending, with stable tie-breaking
        def sort_key(event: TimelineEvent):

            # Parse date safely
            try:
                d = datetime.strptime(event.date[:10], "%Y-%m-%d").date()
            except Exception:
                d = date.min
            priority = EVENT_SORT_ORDER.get(event.eventType, 50)
            return (d, priority, event.title)

        sorted_events = sorted(events, key=sort_key)

        return TimelineResponse(
            productId=product.id,
            productName=product.name,
            events=sorted_events,
            totalEvents=len(sorted_events)
        )

    async def add_custom_lifecycle_event(
        self,
        product_id: str,
        user_id: str,
        data: TimelineEventCreate
    ) -> TimelineEvent:
        """
        Allows adding custom lifecycle milestones (e.g. Service, Maintenance, Screen Repair).
        """
        # Verify ownership
        await product_service.get_product_by_id(product_id, user_id)

        now = datetime.now(timezone.utc)
        doc = {
            "productId": product_id,
            "userId": user_id,
            "eventType": data.eventType,
            "title": data.title.strip(),
            "description": data.description.strip(),
            "date": data.date,
            "category": data.category,
            "status": data.status,
            "icon": data.icon or "wrench",
            "metadata": data.metadata or {},
            "createdAt": now
        }

        result = await self.events_collection.insert_one(doc)
        doc["_id"] = result.inserted_id

        logger.info(f"Custom lifecycle event '{data.title}' added to product {product_id} by user {user_id}")

        return TimelineEvent(
            id=str(doc["_id"]),
            productId=product_id,
            eventType=doc["eventType"],
            title=doc["title"],
            description=doc["description"],
            date=doc["date"],
            category=doc["category"],
            status=doc["status"],
            icon=doc["icon"],
            metadata=doc["metadata"],
            createdAt=now
        )


timeline_service = TimelineService()
