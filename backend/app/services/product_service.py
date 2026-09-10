import logging
from datetime import datetime, timezone
from typing import Optional, List, Dict, Any
from bson import ObjectId
from pymongo import ReturnDocument
from motor.motor_asyncio import AsyncIOMotorDatabase

from app.core.database import db_manager
from app.core.exceptions import AppException, NotFoundException
from app.schemas.product import ProductCreate, ProductUpdate, ProductResponse
from app.services.return_service import (
    calculate_return_deadline,
    calculate_return_status,
    get_verified_seller_policy
)

logger = logging.getLogger("ownit.services.product")


def format_product_doc(doc: Dict[str, Any]) -> ProductResponse:
    """
    Transforms a raw MongoDB document into a typed ProductResponse schema
    with dynamically computed return/replacement status and deadlines.
    """
    return_duration = doc.get("returnDuration")
    return_start_date = doc.get("returnStartDate") or doc.get("purchaseDate")
    return_deadline = doc.get("returnDeadline")
    return_source = doc.get("returnPolicySource")

    # If deadline is missing but duration and start date are known, auto-derive deadline
    if not return_deadline and return_duration and return_start_date:
        return_deadline = calculate_return_deadline(return_start_date, return_duration)

    # Compute return status & remaining days (returns ('Unknown', None) if information is missing)
    return_status, days_remaining = calculate_return_status(return_deadline)

    return ProductResponse(
        id=str(doc["_id"]),
        userId=str(doc["userId"]),
        name=doc["name"],
        brand=doc["brand"],
        model=doc["model"],
        category=doc.get("category", "Other"),
        purchaseDate=doc["purchaseDate"],
        price=float(doc["price"]),
        quantity=int(doc.get("quantity", 1)),
        seller=doc.get("seller"),
        serialNumber=doc.get("serialNumber"),
        imei=doc.get("imei"),
        image=doc.get("image"),
        notes=doc.get("notes"),
        returnDuration=return_duration,
        returnStartDate=doc.get("returnStartDate"),
        returnDeadline=return_deadline,
        returnPolicySource=return_source,
        returnStatus=return_status,
        returnDaysRemaining=days_remaining,
        createdAt=doc.get("createdAt", datetime.now(timezone.utc)),
        updatedAt=doc.get("updatedAt", datetime.now(timezone.utc))
    )


class ProductService:
    """
    Handles CRUD operations and user ownership verification for products in MongoDB.
    """
    @property
    def db(self) -> AsyncIOMotorDatabase:
        database = db_manager.get_db()
        if database is None:
            raise AppException(
                message="Database service is currently offline. Please ensure MongoDB is running.",
                status_code=503,
                error_code="DATABASE_UNAVAILABLE"
            )
        return database

    @property
    def collection(self):
        return self.db["products"]

    async def ensure_indexes(self) -> None:
        """
        Creates compound and single field indexes for optimal query performance and user scoping.
        """
        try:
            await self.collection.create_index(
                [("userId", 1), ("createdAt", -1)],
                name="user_products_created_idx"
            )
            await self.collection.create_index(
                [("userId", 1), ("category", 1)],
                name="user_products_category_idx"
            )
            logger.info("Product indexes ensured in MongoDB.")
        except Exception as exc:
            logger.warning(f"Could not create product indexes: {exc}")

    async def create_product(self, user_id: str, data: ProductCreate) -> ProductResponse:
        """
        Creates a new product record scoped to the authenticated user.
        If return policy is not explicitly provided, checks verified seller policy defaults if available.
        """
        now = datetime.now(timezone.utc)

        return_duration = data.returnDuration
        return_start_date = data.returnStartDate or data.purchaseDate
        return_deadline = data.returnDeadline
        return_source = data.returnPolicySource

        # Check verified seller policy defaults if user didn't specify return info
        if not return_duration and not return_deadline and data.seller:
            seller_policy = get_verified_seller_policy(data.seller)
            if seller_policy:
                return_duration = seller_policy.get("duration")
                return_source = seller_policy.get("source")
                return_deadline = calculate_return_deadline(return_start_date, return_duration)

        # Auto-derive deadline if duration and start date provided
        if not return_deadline and return_duration and return_start_date:
            return_deadline = calculate_return_deadline(return_start_date, return_duration)

        doc = {
            "userId": user_id,
            "name": data.name,
            "brand": data.brand,
            "model": data.model,
            "category": data.category,
            "purchaseDate": data.purchaseDate,
            "price": data.price,
            "quantity": data.quantity,
            "seller": data.seller,
            "serialNumber": data.serialNumber,
            "imei": data.imei,
            "image": data.image,
            "notes": data.notes,
            "returnDuration": return_duration,
            "returnStartDate": data.returnStartDate,
            "returnDeadline": return_deadline,
            "returnPolicySource": return_source,
            "createdAt": now,
            "updatedAt": now
        }

        result = await self.collection.insert_one(doc)
        doc["_id"] = result.inserted_id

        logger.info(f"Product created: '{data.name}' (ID: {doc['_id']}) for user {user_id}")
        return format_product_doc(doc)

    async def get_user_products(
        self,
        user_id: str,
        category: Optional[str] = None,
        search: Optional[str] = None
    ) -> List[ProductResponse]:
        """
        Retrieves all products belonging to the given user, with optional category filter & keyword search.
        """
        query: Dict[str, Any] = {"userId": user_id}

        if category and category.strip() and category != "All":
            query["category"] = category.strip()

        if search and search.strip():
            term = search.strip()
            query["$or"] = [
                {"name": {"$regex": term, "$options": "i"}},
                {"brand": {"$regex": term, "$options": "i"}},
                {"model": {"$regex": term, "$options": "i"}},
                {"serialNumber": {"$regex": term, "$options": "i"}},
                {"seller": {"$regex": term, "$options": "i"}}
            ]

        cursor = self.collection.find(query).sort("createdAt", -1)
        products = []
        async for doc in cursor:
            products.append(format_product_doc(doc))

        return products

    async def get_product_by_id(self, product_id: str, user_id: str) -> ProductResponse:
        """
        Retrieves a single product by ID, strictly enforcing user ownership.
        """
        if not ObjectId.is_valid(product_id):
            raise NotFoundException(
                message=f"Product with ID '{product_id}' was not found.",
                details={"productId": product_id}
            )

        doc = await self.collection.find_one({
            "_id": ObjectId(product_id),
            "userId": user_id
        })

        if not doc:
            raise NotFoundException(
                message=f"Product with ID '{product_id}' was not found or you do not have permission to access it.",
                details={"productId": product_id}
            )

        return format_product_doc(doc)

    async def update_product(
        self,
        product_id: str,
        user_id: str,
        data: ProductUpdate
    ) -> ProductResponse:
        """
        Updates an existing product, strictly enforcing user ownership.
        """
        if not ObjectId.is_valid(product_id):
            raise NotFoundException(
                message=f"Product with ID '{product_id}' was not found.",
                details={"productId": product_id}
            )

        update_dict = {k: v for k, v in data.model_dump().items() if v is not None}
        if not update_dict:
            return await self.get_product_by_id(product_id, user_id)

        # Recalculate deadline if start date or duration changed
        if "returnDuration" in update_dict or "returnStartDate" in update_dict:
            current = await self.collection.find_one({"_id": ObjectId(product_id), "userId": user_id})
            if current:
                start_date = update_dict.get("returnStartDate") or current.get("returnStartDate") or current.get("purchaseDate")
                duration = update_dict.get("returnDuration") or current.get("returnDuration")
                if duration and start_date and "returnDeadline" not in update_dict:
                    update_dict["returnDeadline"] = calculate_return_deadline(start_date, duration)

        update_dict["updatedAt"] = datetime.now(timezone.utc)

        updated_doc = await self.collection.find_one_and_update(
            {"_id": ObjectId(product_id), "userId": user_id},
            {"$set": update_dict},
            return_document=ReturnDocument.AFTER
        )

        if not updated_doc:
            raise NotFoundException(
                message=f"Product with ID '{product_id}' was not found or you do not have permission to update it.",
                details={"productId": product_id}
            )

        logger.info(f"Product updated: ID {product_id} by user {user_id}")
        return format_product_doc(updated_doc)

    async def delete_product(self, product_id: str, user_id: str) -> bool:
        """
        Deletes a product document, strictly enforcing user ownership.
        """
        if not ObjectId.is_valid(product_id):
            raise NotFoundException(
                message=f"Product with ID '{product_id}' was not found.",
                details={"productId": product_id}
            )

        result = await self.collection.delete_one({
            "_id": ObjectId(product_id),
            "userId": user_id
        })

        if result.deleted_count == 0:
            raise NotFoundException(
                message=f"Product with ID '{product_id}' was not found or you do not have permission to delete it.",
                details={"productId": product_id}
            )

        logger.info(f"Product deleted: ID {product_id} by user {user_id}")
        return True


product_service = ProductService()
