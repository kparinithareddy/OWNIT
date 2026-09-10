import logging
from datetime import datetime, timezone
from typing import List, Dict, Any, Optional
from bson import ObjectId
from pymongo import ASCENDING, DESCENDING

from app.core.database import db_manager
from app.core.exceptions import (
    AppException,
    NotFoundException,
    ValidationException,
    UnauthorizedException
)
from app.schemas.service_history import (
    ServiceRecordCreate,
    ServiceRecordUpdate,
    ServiceRecordResponse
)
from app.services.product_service import product_service

logger = logging.getLogger("ownit.services.service_history")


def format_service_doc(doc: Dict[str, Any], product_doc: Optional[Dict[str, Any]] = None, doc_name: Optional[str] = None) -> ServiceRecordResponse:
    """
    Transforms MongoDB document into typed ServiceRecordResponse schema.
    """
    return ServiceRecordResponse(
        id=str(doc["_id"]),
        productId=str(doc["productId"]),
        userId=str(doc["userId"]),
        serviceDate=doc["serviceDate"],
        problem=doc["problem"],
        serviceCenter=doc["serviceCenter"],
        workPerformed=doc["workPerformed"],
        cost=float(doc.get("cost", 0.0) or 0.0),
        warrantyCovered=bool(doc.get("warrantyCovered", False)),
        notes=doc.get("notes"),
        documentId=str(doc["documentId"]) if doc.get("documentId") else None,
        documentName=doc_name or doc.get("documentName"),
        productName=product_doc.get("name") if product_doc else doc.get("productName"),
        productBrand=product_doc.get("brand") if product_doc else doc.get("productBrand"),
        createdAt=doc.get("createdAt", datetime.now(timezone.utc)),
        updatedAt=doc.get("updatedAt", datetime.now(timezone.utc))
    )


class ServiceHistoryService:
    """
    Manages physical repair and servicing history records with strict owner data isolation.
    """

    @property
    def collection(self):
        return db_manager.get_collection("service_records")

    @property
    def documents_collection(self):
        return db_manager.get_collection("documents")

    @property
    def products_collection(self):
        return db_manager.get_collection("products")

    async def ensure_indexes(self) -> None:
        """
        Creates MongoDB indexes for fast lookup and user isolation.
        """
        try:
            col = self.collection
            if col is not None:
                await col.create_index(
                    [("userId", ASCENDING), ("productId", ASCENDING), ("serviceDate", DESCENDING)],
                    name="idx_service_records_user_product_date"
                )
                logger.info("Service history indexes ensured in MongoDB.")
        except Exception as e:
            logger.warning("Could not create service history indexes: %s", e)

    async def create_service_record(
        self,
        user_id: str,
        data: ServiceRecordCreate
    ) -> ServiceRecordResponse:
        """
        Creates a new service/repair record verifying product ownership.
        """
        # Verify product ownership
        product = await product_service.get_product_by_id(data.productId, user_id)

        # Lookup optional document name if attached
        document_name = None
        if data.documentId and ObjectId.is_valid(data.documentId):
            doc = await self.documents_collection.find_one({
                "_id": ObjectId(data.documentId),
                "userId": user_id
            })
            if doc:
                document_name = doc.get("originalFilename")

        now = datetime.now(timezone.utc)
        record_doc = {
            "userId": user_id,
            "productId": data.productId,
            "productName": product.name,
            "productBrand": product.brand,
            "serviceDate": data.serviceDate.strip(),
            "problem": data.problem.strip(),
            "serviceCenter": data.serviceCenter.strip(),
            "workPerformed": data.workPerformed.strip(),
            "cost": float(data.cost or 0.0),
            "warrantyCovered": bool(data.warrantyCovered),
            "notes": data.notes.strip() if data.notes else None,
            "documentId": data.documentId if data.documentId else None,
            "documentName": document_name,
            "createdAt": now,
            "updatedAt": now
        }

        result = await self.collection.insert_one(record_doc)
        record_doc["_id"] = result.inserted_id

        logger.info("Created service record (ID: %s) for product %s by user %s", record_doc["_id"], data.productId, user_id)
        return format_service_doc(record_doc, {"name": product.name, "brand": product.brand}, document_name)

    async def get_service_records_by_product(
        self,
        product_id: str,
        user_id: str
    ) -> List[ServiceRecordResponse]:
        """
        Retrieves all service records for a product, scoped strictly to the authenticated user.
        """
        # Ensure product ownership
        product = await product_service.get_product_by_id(product_id, user_id)

        cursor = self.collection.find({
            "productId": product_id,
            "userId": user_id
        }).sort("serviceDate", DESCENDING)

        records: List[ServiceRecordResponse] = []
        async for doc in cursor:
            records.append(format_service_doc(doc, {"name": product.name, "brand": product.brand}))

        return records

    async def get_service_record_by_id(
        self,
        service_id: str,
        user_id: str
    ) -> ServiceRecordResponse:
        """
        Retrieves a single service record verifying owner isolation.
        """
        if not ObjectId.is_valid(service_id):
            raise NotFoundException(message=f"Service record ID '{service_id}' is invalid.")

        doc = await self.collection.find_one({
            "_id": ObjectId(service_id),
            "userId": user_id
        })
        if not doc:
            raise NotFoundException(message=f"Service record with ID '{service_id}' was not found or access denied.")

        product_doc = await self.products_collection.find_one({"_id": ObjectId(doc["productId"])}) if ObjectId.is_valid(doc["productId"]) else None
        return format_service_doc(doc, product_doc)

    async def update_service_record(
        self,
        service_id: str,
        user_id: str,
        data: ServiceRecordUpdate
    ) -> ServiceRecordResponse:
        """
        Updates an existing service record ensuring owner isolation.
        """
        if not ObjectId.is_valid(service_id):
            raise NotFoundException(message=f"Service record ID '{service_id}' is invalid.")

        existing = await self.collection.find_one({
            "_id": ObjectId(service_id),
            "userId": user_id
        })
        if not existing:
            raise NotFoundException(message=f"Service record with ID '{service_id}' was not found or access denied.")

        update_dict: Dict[str, Any] = {"updatedAt": datetime.now(timezone.utc)}
        data_dump = data.model_dump(exclude_unset=True)

        for key, val in data_dump.items():
            if val is not None:
                if isinstance(val, str):
                    val = val.strip()
                update_dict[key] = val

        # If documentId was updated, refresh document name
        if "documentId" in update_dict and update_dict["documentId"]:
            if ObjectId.is_valid(update_dict["documentId"]):
                doc = await self.documents_collection.find_one({
                    "_id": ObjectId(update_dict["documentId"]),
                    "userId": user_id
                })
                update_dict["documentName"] = doc.get("originalFilename") if doc else None
            else:
                update_dict["documentName"] = None

        await self.collection.update_one(
            {"_id": ObjectId(service_id), "userId": user_id},
            {"$set": update_dict}
        )

        updated_doc = await self.collection.find_one({"_id": ObjectId(service_id)})
        product_doc = await self.products_collection.find_one({"_id": ObjectId(updated_doc["productId"])}) if ObjectId.is_valid(updated_doc["productId"]) else None
        return format_service_doc(updated_doc, product_doc)

    async def delete_service_record(
        self,
        service_id: str,
        user_id: str
    ) -> bool:
        """
        Deletes a service record belonging to the authenticated user.
        """
        if not ObjectId.is_valid(service_id):
            raise NotFoundException(message=f"Service record ID '{service_id}' is invalid.")

        result = await self.collection.delete_one({
            "_id": ObjectId(service_id),
            "userId": user_id
        })
        if result.deleted_count == 0:
            raise NotFoundException(message=f"Service record with ID '{service_id}' was not found or access denied.")

        logger.info("Deleted service record %s for user %s", service_id, user_id)
        return True


service_history_service = ServiceHistoryService()
