import logging
from datetime import datetime, timezone
from typing import List, Optional, Dict, Any
from bson import ObjectId
from pymongo import ASCENDING, DESCENDING, ReturnDocument

from app.core.database import db_manager
from app.core.exceptions import NotFoundException
from app.schemas.maintenance import (
    MaintenanceCreate,
    MaintenanceUpdate,
    MaintenanceResponse,
    MaintenanceRecommendation
)
from app.services.product_service import product_service

logger = logging.getLogger("ownit.services.maintenance")

# Category-specific preventive care guidelines for future AI extension
# Rule: Do not pretend that maintenance recommendations are manufacturer-approved unless sourced.
CATEGORY_RECOMMENDATIONS = {
    "Air Conditioner": [
        {
            "id": "rec-ac-filter",
            "category": "Air Conditioner",
            "title": "Clean Mesh Air Filters",
            "description": "Rinse nylon dust filters under lukewarm running water to maintain cooling efficiency and airflow.",
            "suggestedIntervalMonths": 3,
            "source": "Standard HVAC Preventive Care Checklist",
            "isManufacturerApproved": False,
            "disclaimer": "General preventive care guideline. Consult your specific AC brand user manual for model-exact cleaning procedures."
        },
        {
            "id": "rec-ac-service",
            "category": "Air Conditioner",
            "title": "Annual Deep Chemical Wash & Gas Inspection",
            "description": "Professional indoor/outdoor coil foam wash and refrigerant pressure check prior to peak summer.",
            "suggestedIntervalMonths": 12,
            "source": "General Appliance Care Guidelines",
            "isManufacturerApproved": False,
            "disclaimer": "General industry practice. Seek authorized service technicians to preserve active warranties."
        }
    ],
    "Washing Machine": [
        {
            "id": "rec-wm-tub",
            "category": "Washing Machine",
            "title": "Run Tub Clean Cycle with Descaler",
            "description": "Run an empty hot water tub-clean cycle with descaling powder to dissolve detergent residue and prevent odors.",
            "suggestedIntervalMonths": 1,
            "source": "General Laundry Appliance Maintenance Guide",
            "isManufacturerApproved": False,
            "disclaimer": "General preventive care guideline. Check your washer handbook for recommended descaling agents."
        },
        {
            "id": "rec-wm-filter",
            "category": "Washing Machine",
            "title": "Clean Coin Trap & Drain Pump Filter",
            "description": "Unscrew the bottom-front drain filter to remove trapped lint, pins, and sediment.",
            "suggestedIntervalMonths": 6,
            "source": "Preventive Care Checklist",
            "isManufacturerApproved": False,
            "disclaimer": "General maintenance advice. Ensure appliance is powered off before opening drain cap."
        }
    ],
    "Refrigerator": [
        {
            "id": "rec-fridge-coils",
            "category": "Refrigerator",
            "title": "De-dust Rear Condenser Coils",
            "description": "Gently vacuum or brush dust from rear condenser coils to reduce compressor workload and energy consumption.",
            "suggestedIntervalMonths": 6,
            "source": "Energy Conservation & Appliance Care Checklist",
            "isManufacturerApproved": False,
            "disclaimer": "General energy-saving guideline. Disconnect power cord prior to cleaning rear coils."
        },
        {
            "id": "rec-fridge-gasket",
            "category": "Refrigerator",
            "title": "Inspect & Wipe Door Rubber Gaskets",
            "description": "Wipe door seal gaskets with warm soapy water to ensure airtight seal and prevent cool air leakage.",
            "suggestedIntervalMonths": 6,
            "source": "General Refrigerator Best Practices",
            "isManufacturerApproved": False,
            "disclaimer": "Standard maintenance practice. Replace warped seals if cool air escapes."
        }
    ],
    "Laptop": [
        {
            "id": "rec-laptop-dust",
            "category": "Laptop",
            "title": "Air Vent & Fan De-dusting",
            "description": "Use compressed air to clear intake vents and cooling fans from accumulated lint to prevent thermal throttling.",
            "suggestedIntervalMonths": 6,
            "source": "Computer Hardware Longevity Guide",
            "isManufacturerApproved": False,
            "disclaimer": "General IT maintenance practice. Do not open sealed chassis without checking warranty conditions."
        },
        {
            "id": "rec-laptop-battery",
            "category": "Laptop",
            "title": "Battery Health & Calibration Check",
            "description": "Review battery maximum capacity health percentage and enable smart charging thresholds (80% limit).",
            "suggestedIntervalMonths": 6,
            "source": "Battery Care General Guidelines",
            "isManufacturerApproved": False,
            "disclaimer": "Standard lithium battery maintenance guideline."
        }
    ],
    "Mobile": [
        {
            "id": "rec-phone-port",
            "category": "Mobile",
            "title": "Clean Charging Port & Speaker Grille",
            "description": "Gently remove pocket lint from USB-C/Lightning charging port using an anti-static pick or dry soft brush.",
            "suggestedIntervalMonths": 3,
            "source": "Mobile Device Best Practices",
            "isManufacturerApproved": False,
            "disclaimer": "General device care practice. Never insert metallic needles or conductive tools into charging pins."
        }
    ],
    "TV": [
        {
            "id": "rec-tv-cleaning",
            "category": "TV",
            "title": "Screen Microfiber Dusting & Air Vent Inspection",
            "description": "Wipe television panel with dry anti-static microfiber cloth without harsh chemicals.",
            "suggestedIntervalMonths": 3,
            "source": "Consumer Electronics Care Guide",
            "isManufacturerApproved": False,
            "disclaimer": "General display maintenance guideline. Never spray liquids directly onto television panels."
        }
    ]
}


def format_maintenance_doc(doc: Dict[str, Any]) -> MaintenanceResponse:
    return MaintenanceResponse(
        id=str(doc["_id"]),
        productId=str(doc["productId"]),
        userId=str(doc["userId"]),
        title=doc["title"],
        description=doc.get("description", ""),
        date=doc["date"],
        type=doc.get("type", "Routine Servicing"),
        status=doc.get("status", "Completed"),
        notes=doc.get("notes"),
        cost=float(doc["cost"]) if doc.get("cost") is not None else None,
        serviceProvider=doc.get("serviceProvider"),
        documentId=doc.get("documentId"),
        nextDueDate=doc.get("nextDueDate"),
        documentName=doc.get("documentName"),
        createdAt=doc.get("createdAt", datetime.now(timezone.utc)),
        updatedAt=doc.get("updatedAt", datetime.now(timezone.utc))
    )


class MaintenanceService:
    @property
    def collection(self):
        return db_manager.get_collection("maintenance_records")

    async def ensure_indexes(self):
        try:
            col = self.collection
            await col.create_index(
                [("productId", ASCENDING), ("userId", ASCENDING), ("date", DESCENDING)],
                name="idx_maintenance_product_user_date"
            )
            logger.info("Maintenance records indexes ensured in MongoDB.")
        except Exception as e:
            logger.warning(f"Could not create maintenance indexes: {e}")

    async def create_record(self, user_id: str, data: MaintenanceCreate) -> MaintenanceResponse:
        """
        Creates a maintenance log entry strictly scoped to product owner.
        """
        # Verify user owns the product
        await product_service.get_product_by_id(data.productId, user_id)

        now = datetime.now(timezone.utc)
        doc = {
            "productId": data.productId,
            "userId": user_id,
            "title": data.title.strip(),
            "description": data.description.strip(),
            "date": data.date,
            "type": data.type,
            "status": data.status,
            "notes": data.notes.strip() if data.notes else None,
            "cost": data.cost,
            "serviceProvider": data.serviceProvider.strip() if data.serviceProvider else None,
            "documentId": data.documentId,
            "nextDueDate": data.nextDueDate,
            "createdAt": now,
            "updatedAt": now
        }

        result = await self.collection.insert_one(doc)
        doc["_id"] = result.inserted_id

        logger.info(f"Maintenance record '{data.title}' created for product {data.productId}")
        return format_maintenance_doc(doc)

    async def get_records_by_product(self, product_id: str, user_id: str) -> List[MaintenanceResponse]:
        """
        Lists all maintenance history records for a product, sorted newest date first.
        """
        await product_service.get_product_by_id(product_id, user_id)

        cursor = self.collection.find({"productId": product_id, "userId": user_id}).sort("date", DESCENDING)
        records = []
        async for doc in cursor:
            records.append(format_maintenance_doc(doc))
        return records

    async def get_record_by_id(self, record_id: str, user_id: str) -> MaintenanceResponse:
        """
        Fetches a specific maintenance record verifying user ownership.
        """
        if not ObjectId.is_valid(record_id):
            raise NotFoundException(message=f"Maintenance record '{record_id}' not found.")

        doc = await self.collection.find_one({"_id": ObjectId(record_id), "userId": user_id})
        if not doc:
            raise NotFoundException(message=f"Maintenance record '{record_id}' not found or access denied.")

        return format_maintenance_doc(doc)

    async def update_record(self, record_id: str, user_id: str, data: MaintenanceUpdate) -> MaintenanceResponse:
        """
        Updates an existing maintenance record.
        """
        if not ObjectId.is_valid(record_id):
            raise NotFoundException(message=f"Maintenance record '{record_id}' not found.")

        update_dict = {k: v for k, v in data.model_dump().items() if v is not None}
        if not update_dict:
            return await self.get_record_by_id(record_id, user_id)

        update_dict["updatedAt"] = datetime.now(timezone.utc)

        updated_doc = await self.collection.find_one_and_update(
            {"_id": ObjectId(record_id), "userId": user_id},
            {"$set": update_dict},
            return_document=ReturnDocument.AFTER
        )

        if not updated_doc:
            raise NotFoundException(message=f"Maintenance record '{record_id}' not found or access denied.")

        return format_maintenance_doc(updated_doc)

    async def delete_record(self, record_id: str, user_id: str) -> bool:
        """
        Deletes a maintenance record.
        """
        if not ObjectId.is_valid(record_id):
            raise NotFoundException(message=f"Maintenance record '{record_id}' not found.")

        result = await self.collection.delete_one({"_id": ObjectId(record_id), "userId": user_id})
        if result.deleted_count == 0:
            raise NotFoundException(message=f"Maintenance record '{record_id}' not found or access denied.")

        return True

    async def get_recommendations_for_product(self, product_id: str, user_id: str) -> List[MaintenanceRecommendation]:
        """
        Returns structured maintenance recommendations based on the product category.
        Enforces clear sourcing transparency without claiming unverified OEM endorsement.
        """
        product = await product_service.get_product_by_id(product_id, user_id)
        cat = product.category
        recs_data = CATEGORY_RECOMMENDATIONS.get(cat, [
            {
                "id": f"rec-{product.id}-general",
                "category": cat,
                "title": "General Periodic Inspection & Cleaning",
                "description": f"Inspect {product.name} physical condition, clean exterior, and check cables for wear.",
                "suggestedIntervalMonths": 6,
                "source": "General Consumer Electronics & Appliance Care",
                "isManufacturerApproved": False,
                "disclaimer": "General preventive care guideline. Not verified with specific OEM manual."
            }
        ])

        return [MaintenanceRecommendation(**item) for item in recs_data]


maintenance_service = MaintenanceService()
