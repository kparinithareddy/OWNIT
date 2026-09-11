import os
import logging
import re
from datetime import datetime, timezone, timedelta
from typing import Optional, List, Dict, Any, Set
from bson import ObjectId
from pymongo import ReturnDocument, ASCENDING, DESCENDING
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
                [("userId", 1), ("category", 1), ("brand", 1)],
                name="user_products_category_brand_idx"
            )
            await self.collection.create_index(
                [("userId", 1), ("brand", 1)],
                name="user_products_brand_idx"
            )
            await self.collection.create_index(
                [("userId", 1), ("name", 1)],
                name="user_products_name_idx"
            )
            await self.collection.create_index(
                [("userId", 1), ("model", 1)],
                name="user_products_model_idx"
            )
            await self.collection.create_index(
                [("userId", 1), ("serialNumber", 1)],
                name="user_products_serial_idx"
            )
            logger.info("Product indexes ensured in MongoDB.")
        except Exception as exc:
            logger.warning(f"Could not create product indexes: {exc}")

    async def get_user_brands(self, user_id: str) -> List[str]:
        """
        Retrieves unique product brands recorded by the authenticated user.
        """
        raw_brands = await self.collection.distinct("brand", {"userId": user_id})
        clean_brands = {b.strip() for b in raw_brands if b and b.strip()}
        return sorted(list(clean_brands))

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
        brand: Optional[str] = None,
        search: Optional[str] = None,
        warranty_status: Optional[str] = None,
        return_status: Optional[str] = None,
        maintenance_status: Optional[str] = None,
        sort_by: Optional[str] = "createdAt",
        sort_order: Optional[str] = "desc"
    ) -> List[ProductResponse]:
        """
        Retrieves all products belonging to the given user with multi-field search,
        category, brand, warranty status, return period, and maintenance status filters.
        Optimized with indexed queries and no unnecessary collection scans.
        """
        query: Dict[str, Any] = {"userId": user_id}

        # 1. Category Filter
        if category and category.strip() and category != "All":
            query["category"] = category.strip()

        # 2. Brand Filter
        if brand and brand.strip() and brand != "All":
            query["brand"] = {"$regex": f"^{re.escape(brand.strip())}$", "$options": "i"}

        # 3. Multi-field Keyword Search (product name, brand, model, serial number)
        if search and search.strip():
            term = re.escape(search.strip())
            query["$or"] = [
                {"name": {"$regex": term, "$options": "i"}},
                {"brand": {"$regex": term, "$options": "i"}},
                {"model": {"$regex": term, "$options": "i"}},
                {"serialNumber": {"$regex": term, "$options": "i"}},
                {"seller": {"$regex": term, "$options": "i"}}
            ]

        # 4. Warranty Status Filter
        if warranty_status and warranty_status.lower() != "all":
            w_col = self.db["warranties"]
            today = datetime.now(timezone.utc).date()
            today_str = today.isoformat()
            exp_soon_threshold = (today + timedelta(days=30)).isoformat()

            status_key = warranty_status.lower().strip()
            if status_key == "active":
                cursor = w_col.find({
                    "userId": user_id,
                    "expiryDate": {"$gt": exp_soon_threshold}
                }, {"productId": 1})
                active_pids = [doc["productId"] async for doc in cursor if doc.get("productId")]
                valid_oids = [ObjectId(p) for p in active_pids if ObjectId.is_valid(p)]
                query["_id"] = {"$in": valid_oids}

            elif status_key == "expiring_soon":
                cursor = w_col.find({
                    "userId": user_id,
                    "expiryDate": {"$gte": today_str, "$lte": exp_soon_threshold}
                }, {"productId": 1})
                expiring_pids = [doc["productId"] async for doc in cursor if doc.get("productId")]
                valid_oids = [ObjectId(p) for p in expiring_pids if ObjectId.is_valid(p)]
                query["_id"] = {"$in": valid_oids}

            elif status_key == "expired":
                # Find product IDs where all warranties are expired (< today) and none are active
                active_cursor = w_col.find({
                    "userId": user_id,
                    "expiryDate": {"$gte": today_str}
                }, {"productId": 1})
                active_pids = {doc["productId"] async for doc in active_cursor if doc.get("productId")}

                exp_cursor = w_col.find({
                    "userId": user_id,
                    "expiryDate": {"$lt": today_str}
                }, {"productId": 1})
                exp_pids = {doc["productId"] async for doc in exp_cursor if doc.get("productId")}

                expired_only_pids = exp_pids - active_pids
                valid_oids = [ObjectId(p) for p in expired_only_pids if ObjectId.is_valid(p)]
                query["_id"] = {"$in": valid_oids}

        # 5. Return Status Filter
        if return_status and return_status.lower() != "all":
            today_str = datetime.now(timezone.utc).date().isoformat()
            ret_key = return_status.lower().strip()
            if "$and" not in query:
                query["$and"] = []

            if ret_key == "active":
                query["$and"].append({
                    "$or": [
                        {"returnDeadline": {"$gte": today_str}},
                        {"returnStatus": "Active"}
                    ]
                })
            elif ret_key == "expired":
                query["$and"].append({
                    "$or": [
                        {"returnDeadline": {"$lt": today_str}},
                        {"returnStatus": "Expired"}
                    ]
                })

        # 6. Maintenance Status Filter
        if maintenance_status and maintenance_status.lower() != "all":
            m_col = self.db["maintenance_records"]
            today = datetime.now(timezone.utc).date()
            today_str = today.isoformat()
            m_key = maintenance_status.lower().strip()

            if m_key in ("due", "due_soon"):
                week_later_str = (today + timedelta(days=7)).isoformat()
                m_cursor = m_col.find({
                    "userId": user_id,
                    "status": {"$ne": "Completed"},
                    "nextDueDate": {"$gte": today_str, "$lte": week_later_str}
                }, {"productId": 1})
                m_pids = [doc["productId"] async for doc in m_cursor if doc.get("productId")]
                valid_oids = [ObjectId(p) for p in m_pids if ObjectId.is_valid(p)]

                if "_id" in query and "$in" in query["_id"]:
                    query["_id"]["$in"] = list(set(query["_id"]["$in"]) & set(valid_oids))
                else:
                    query["_id"] = {"$in": valid_oids}

            elif m_key == "needs_attention":
                week_later_str = (today + timedelta(days=7)).isoformat()
                m_cursor = m_col.find({
                    "userId": user_id,
                    "status": {"$ne": "Completed"},
                    "nextDueDate": {"$lte": week_later_str}
                }, {"productId": 1})
                m_pids = [doc["productId"] async for doc in m_cursor if doc.get("productId")]
                valid_oids = [ObjectId(p) for p in m_pids if ObjectId.is_valid(p)]

                if "_id" in query and "$in" in query["_id"]:
                    query["_id"]["$in"] = list(set(query["_id"]["$in"]) & set(valid_oids))
                else:
                    query["_id"] = {"$in": valid_oids}

            elif m_key == "overdue":
                m_cursor = m_col.find({
                    "userId": user_id,
                    "status": {"$ne": "Completed"},
                    "nextDueDate": {"$lt": today_str}
                }, {"productId": 1})
                m_pids = [doc["productId"] async for doc in m_cursor if doc.get("productId")]
                valid_oids = [ObjectId(p) for p in m_pids if ObjectId.is_valid(p)]

                if "_id" in query and "$in" in query["_id"]:
                    query["_id"]["$in"] = list(set(query["_id"]["$in"]) & set(valid_oids))
                else:
                    query["_id"] = {"$in": valid_oids}

            elif m_key == "up_to_date":
                # Exclude products that have pending/overdue maintenance tasks
                overdue_cursor = m_col.find({
                    "userId": user_id,
                    "status": {"$ne": "Completed"},
                    "nextDueDate": {"$lte": today_str}
                }, {"productId": 1})
                overdue_pids = {doc["productId"] async for doc in overdue_cursor if doc.get("productId")}
                overdue_oids = [ObjectId(p) for p in overdue_pids if ObjectId.is_valid(p)]
                if overdue_oids:
                    if "_id" in query and "$nin" in query["_id"]:
                        query["_id"]["$nin"].extend(overdue_oids)
                    else:
                        query["_id"] = {"$nin": overdue_oids}

        # 7. Sorting
        valid_sort_fields = {
            "createdAt": "createdAt",
            "name": "name",
            "price": "price",
            "purchaseDate": "purchaseDate",
            "brand": "brand"
        }
        db_sort_field = valid_sort_fields.get(sort_by, "createdAt")
        direction = ASCENDING if str(sort_order).lower() == "asc" else DESCENDING

        cursor = self.collection.find(query).sort(db_sort_field, direction)
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
        Deletes a product document and all associated sub-resources (warranties,
        documents, maintenance records, service records, chat messages, notifications),
        strictly enforcing user ownership and data isolation.
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

        # Cascading deletion of associated product records
        pid_query = {"productId": product_id, "userId": user_id}
        await self.db["warranties"].delete_many(pid_query)
        await self.db["maintenance_records"].delete_many(pid_query)
        await self.db["service_records"].delete_many(pid_query)
        await self.db["chat_messages"].delete_many(pid_query)
        await self.db["notifications"].delete_many(pid_query)

        # For documents, also clean up physical files
        doc_cursor = self.db["documents"].find(pid_query)
        async for doc in doc_cursor:
            storage_path = doc.get("storagePath")
            if storage_path and os.path.exists(storage_path):
                try:
                    os.remove(storage_path)
                except Exception as e:
                    logger.warning(f"Failed to delete document file {storage_path}: {e}")
        await self.db["documents"].delete_many(pid_query)

        logger.info(f"Product deleted: ID {product_id} with all cascaded dependencies by user {user_id}")
        return True


product_service = ProductService()
