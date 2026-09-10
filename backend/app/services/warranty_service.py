import logging
import re
from datetime import datetime, timezone, date, timedelta
from typing import Optional, List, Dict, Any, Tuple
from bson import ObjectId
from motor.motor_asyncio import AsyncIOMotorDatabase

from app.core.database import db_manager
from app.core.exceptions import (
    AppException,
    NotFoundException,
    ValidationException,
    UnauthorizedException
)
from app.schemas.warranty import (
    WarrantyCreate,
    WarrantyUpdate,
    WarrantyResponse,
    WarrantySummaryResponse
)

logger = logging.getLogger("ownit.services.warranty")


def calculate_warranty_status(expiry_date_str: str) -> Tuple[str, int, str]:
    """
    Computes real-time warranty status, remaining days, and UI color based on current UTC date.
    
    Status Rules:
    - Expired: Expiry date is strictly in the past (< today)
    - Expiring Soon: Expiry is within 30 days (0 <= days <= 30)
    - Active: Expiry is more than 30 days in the future (> 30)
    """
    try:
        if isinstance(expiry_date_str, datetime):
            exp_date = expiry_date_str.date()
        elif isinstance(expiry_date_str, date):
            exp_date = expiry_date_str
        else:
            # Parse ISO YYYY-MM-DD
            clean_str = str(expiry_date_str).split("T")[0]
            exp_date = datetime.strptime(clean_str, "%Y-%m-%d").date()
    except Exception:
        # Fallback if unparseable
        return "Active", 365, "green"

    today = datetime.now(timezone.utc).date()
    days_remaining = (exp_date - today).days

    if days_remaining < 0:
        return "Expired", days_remaining, "red"
    elif days_remaining <= 30:
        return "Expiring Soon", days_remaining, "amber"
    else:
        return "Active", days_remaining, "green"


def calculate_expiry_date(start_date_str: str, duration_str: Optional[str] = None) -> str:
    """
    Calculates target expiry date from start date and duration description.
    Supports years, months, and days. Defaults to 1 Year (12 months).
    """
    try:
        clean_str = str(start_date_str).split("T")[0]
        start_dt = datetime.strptime(clean_str, "%Y-%m-%d").date()
    except Exception:
        start_dt = datetime.now(timezone.utc).date()

    if not duration_str:
        # Default: 1 Year
        try:
            exp_dt = start_dt.replace(year=start_dt.year + 1)
        except ValueError:
            exp_dt = start_dt + timedelta(days=365)
        return exp_dt.strftime("%Y-%m-%d")

    dur_lower = duration_str.lower().strip()

    # Match years (e.g. "2 Years", "3 yr", "5-year")
    year_match = re.search(r"(\d+)\s*(?:year|yr|y)", dur_lower)
    if year_match:
        years = int(year_match.group(1))
        try:
            exp_dt = start_dt.replace(year=start_dt.year + years)
        except ValueError:
            exp_dt = start_dt + timedelta(days=365 * years)
        return exp_dt.strftime("%Y-%m-%d")

    # Match months (e.g. "24 Months", "6 mo", "18 m")
    month_match = re.search(r"(\d+)\s*(?:month|mo|m)", dur_lower)
    if month_match:
        months = int(month_match.group(1))
        # Simple month addition math
        new_year = start_dt.year + (start_dt.month + months - 1) // 12
        new_month = (start_dt.month + months - 1) % 12 + 1
        try:
            exp_dt = start_dt.replace(year=new_year, month=new_month)
        except ValueError:
            # Handle month end day overflow (e.g. Feb 30 -> Feb 28)
            exp_dt = (start_dt.replace(year=new_year, month=new_month, day=1) + timedelta(days=31)).replace(day=1) - timedelta(days=1)
        return exp_dt.strftime("%Y-%m-%d")

    # Match days (e.g. "90 Days")
    day_match = re.search(r"(\d+)\s*(?:day|d)", dur_lower)
    if day_match:
        days = int(day_match.group(1))
        exp_dt = start_dt + timedelta(days=days)
        return exp_dt.strftime("%Y-%m-%d")

    # Fallback to 1 Year
    try:
        exp_dt = start_dt.replace(year=start_dt.year + 1)
    except ValueError:
        exp_dt = start_dt + timedelta(days=365)
    return exp_dt.strftime("%Y-%m-%d")


def format_warranty_doc(doc: Dict[str, Any], product_info: Optional[Dict[str, Any]] = None) -> WarrantyResponse:
    """
    Transforms MongoDB warranty document into typed WarrantyResponse with dynamic status.
    """
    expiry_str = str(doc.get("expiryDate", ""))
    status, days_remaining, status_color = calculate_warranty_status(expiry_str)

    return WarrantyResponse(
        id=str(doc["_id"]),
        productId=str(doc["productId"]),
        userId=str(doc["userId"]),
        productName=product_info.get("name") if product_info else doc.get("productName"),
        productBrand=product_info.get("brand") if product_info else doc.get("productBrand"),
        productCategory=product_info.get("category") if product_info else doc.get("productCategory"),
        type=doc.get("type", "Comprehensive Warranty"),
        provider=doc.get("provider"),
        duration=doc.get("duration"),
        startDate=str(doc.get("startDate", "")),
        expiryDate=expiry_str,
        status=status,
        daysRemaining=days_remaining,
        statusColor=status_color,
        benefits=doc.get("benefits"),
        exclusions=doc.get("exclusions"),
        conditions=doc.get("conditions"),
        claimProcedure=doc.get("claimProcedure"),
        requiredDocuments=doc.get("requiredDocuments", []),
        serviceInformation=doc.get("serviceInformation"),
        createdAt=doc.get("createdAt", datetime.now(timezone.utc)),
        updatedAt=doc.get("updatedAt", datetime.now(timezone.utc))
    )


class WarrantyService:
    """
    Service managing multi-component warranty records, persistence, and dynamic status computation.
    """
    @property
    def db(self) -> AsyncIOMotorDatabase:
        database = db_manager.get_db()
        if database is None:
            raise AppException(
                message="Database service is currently offline.",
                status_code=503,
                error_code="DATABASE_UNAVAILABLE"
            )
        return database

    @property
    def collection(self):
        return self.db["warranties"]

    @property
    def products_collection(self):
        return self.db["products"]

    async def ensure_indexes(self) -> None:
        """Creates MongoDB indexes for fast lookups."""
        try:
            await self.collection.create_index(
                [("userId", 1), ("productId", 1)],
                name="user_product_warranties_idx"
            )
            await self.collection.create_index(
                [("userId", 1), ("expiryDate", 1)],
                name="user_warranty_expiry_idx"
            )
            logger.info("Warranty indexes ensured in MongoDB.")
        except Exception as exc:
            logger.warning(f"Could not create warranty indexes: {exc}")

    async def create_warranty(self, user_id: str, data: WarrantyCreate) -> WarrantyResponse:
        """
        Creates a new warranty component attached to a product belonging to user_id.
        """
        if not ObjectId.is_valid(data.productId):
            raise NotFoundException(message=f"Product '{data.productId}' not found.")

        # 1. Verify Product Ownership
        product_doc = await self.products_collection.find_one({
            "_id": ObjectId(data.productId),
            "userId": user_id
        })
        if not product_doc:
            raise NotFoundException(
                message=f"Product with ID '{data.productId}' was not found or access is denied.",
                details={"productId": data.productId}
            )

        # 2. Compute Expiry Date if omitted or calculate from duration
        start_date = data.startDate.strip()
        expiry_date = data.expiryDate.strip() if data.expiryDate else calculate_expiry_date(start_date, data.duration)

        now = datetime.now(timezone.utc)
        warranty_doc = {
            "userId": user_id,
            "productId": str(product_doc["_id"]),
            "productName": product_doc.get("name"),
            "productBrand": product_doc.get("brand"),
            "productCategory": product_doc.get("category"),
            "type": data.type.strip() if data.type else "Comprehensive Warranty",
            "provider": data.provider.strip() if data.provider else (product_doc.get("brand") or "Manufacturer"),
            "duration": data.duration.strip() if data.duration else None,
            "startDate": start_date,
            "expiryDate": expiry_date,
            "benefits": data.benefits.strip() if data.benefits else None,
            "exclusions": data.exclusions.strip() if data.exclusions else None,
            "conditions": data.conditions.strip() if data.conditions else None,
            "claimProcedure": data.claimProcedure.strip() if data.claimProcedure else None,
            "requiredDocuments": data.requiredDocuments or [],
            "serviceInformation": data.serviceInformation.strip() if data.serviceInformation else None,
            "createdAt": now,
            "updatedAt": now
        }

        result = await self.collection.insert_one(warranty_doc)
        warranty_doc["_id"] = result.inserted_id

        logger.info(f"Created warranty component '{warranty_doc['type']}' (ID: {warranty_doc['_id']}) for product {data.productId}")
        return format_warranty_doc(warranty_doc, product_doc)

    async def get_warranty_by_id(self, warranty_id: str, user_id: str) -> WarrantyResponse:
        """Retrieves single warranty ensuring owner isolation."""
        if not ObjectId.is_valid(warranty_id):
            raise NotFoundException(message=f"Warranty ID '{warranty_id}' is invalid.")

        doc = await self.collection.find_one({
            "_id": ObjectId(warranty_id),
            "userId": user_id
        })
        if not doc:
            raise NotFoundException(message=f"Warranty record '{warranty_id}' not found.")

        product_doc = await self.products_collection.find_one({"_id": ObjectId(doc["productId"])})
        return format_warranty_doc(doc, product_doc)

    async def update_warranty(self, warranty_id: str, user_id: str, data: WarrantyUpdate) -> WarrantyResponse:
        """Updates warranty details, recalculating expiry/status if dates change."""
        if not ObjectId.is_valid(warranty_id):
            raise NotFoundException(message=f"Warranty ID '{warranty_id}' is invalid.")

        existing = await self.collection.find_one({
            "_id": ObjectId(warranty_id),
            "userId": user_id
        })
        if not existing:
            raise NotFoundException(message=f"Warranty record '{warranty_id}' not found.")

        update_dict: Dict[str, Any] = {"updatedAt": datetime.now(timezone.utc)}
        data_dump = data.model_dump(exclude_unset=True)

        for key, val in data_dump.items():
            if val is not None:
                if isinstance(val, str):
                    val = val.strip()
                update_dict[key] = val

        # If startDate or duration updated and expiryDate was not explicitly sent, recalculate expiry
        start_date = update_dict.get("startDate", existing.get("startDate"))
        duration = update_dict.get("duration", existing.get("duration"))
        if ("startDate" in update_dict or "duration" in update_dict) and "expiryDate" not in update_dict:
            update_dict["expiryDate"] = calculate_expiry_date(start_date, duration)

        await self.collection.update_one(
            {"_id": ObjectId(warranty_id)},
            {"$set": update_dict}
        )

        updated_doc = await self.collection.find_one({"_id": ObjectId(warranty_id)})
        product_doc = await self.products_collection.find_one({"_id": ObjectId(updated_doc["productId"])})
        return format_warranty_doc(updated_doc, product_doc)

    async def delete_warranty(self, warranty_id: str, user_id: str) -> None:
        """Deletes a warranty component belonging to user."""
        if not ObjectId.is_valid(warranty_id):
            raise NotFoundException(message=f"Warranty ID '{warranty_id}' is invalid.")

        result = await self.collection.delete_one({
            "_id": ObjectId(warranty_id),
            "userId": user_id
        })
        if result.deleted_count == 0:
            raise NotFoundException(message=f"Warranty record '{warranty_id}' was not found.")

    async def get_user_warranties(
        self,
        user_id: str,
        product_id: Optional[str] = None,
        status_filter: Optional[str] = None
    ) -> List[WarrantyResponse]:
        """Retrieves user warranties with optional product & status filtering."""
        query: Dict[str, Any] = {"userId": user_id}
        if product_id and product_id != "All" and ObjectId.is_valid(product_id):
            query["productId"] = product_id

        cursor = self.collection.find(query).sort("expiryDate", 1)
        docs = await cursor.to_list(length=1000)

        # Batch lookup products for titles
        product_ids = [ObjectId(d["productId"]) for d in docs if ObjectId.is_valid(d.get("productId", ""))]
        products_map = {}
        if product_ids:
            prod_cursor = self.products_collection.find({"_id": {"$in": product_ids}})
            for p in await prod_cursor.to_list(length=len(product_ids)):
                products_map[str(p["_id"])] = p

        results = []
        for d in docs:
            prod_info = products_map.get(str(d.get("productId")))
            w_res = format_warranty_doc(d, prod_info)
            if status_filter and status_filter != "All":
                if w_res.status.lower() != status_filter.lower():
                    continue
            results.append(w_res)

        return results

    async def get_product_warranties(self, product_id: str, user_id: str) -> List[WarrantyResponse]:
        """Convenience method to list all warranty components for a single product."""
        return await self.get_user_warranties(user_id=user_id, product_id=product_id)

    async def get_warranty_summary(self, user_id: str) -> WarrantySummaryResponse:
        """Computes aggregate warranty status counts for dashboard."""
        all_warranties = await self.get_user_warranties(user_id=user_id)

        active = 0
        expiring_soon = 0
        expired = 0
        expiring_soon_items = []

        for w in all_warranties:
            if w.status == "Active":
                active += 1
            elif w.status == "Expiring Soon":
                expiring_soon += 1
                expiring_soon_items.append(w)
            elif w.status == "Expired":
                expired += 1

        return WarrantySummaryResponse(
            totalWarranties=len(all_warranties),
            activeCount=active,
            expiringSoonCount=expiring_soon,
            expiredCount=expired,
            expiringSoonItems=expiring_soon_items
        )


warranty_service = WarrantyService()
