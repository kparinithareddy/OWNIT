import logging
import re
from datetime import datetime, timezone, timedelta
from typing import List, Dict, Any, Optional, Tuple
from app.core.database import db_manager
from app.schemas.sources import SourceReference
from app.services.ai.source_service import source_service

logger = logging.getLogger("ownit.services.ai.retrieval")


class IntentClassifier:
    """
    Classifies user message intent using deterministic keyword and regex matching.
    """

    @staticmethod
    def classify_intent(query: str) -> str:
        q = query.lower().strip()

        # Life Score queries
        if any(w in q for w in ["life score", "lifescore", "health score", "lowest score", "highest score", "device health"]):
            return "life_score"

        # Claim queries (check before general warranty)
        if any(w in q for w in ["claim", "file claim", "claim procedure", "draft claim", "claim assistant"]):
            return "claim"

        # Return / refund queries
        if any(w in q for w in ["return", "replacement", "refund", "return window", "return policy", "return deadline"]):
            return "return"

        # Warranty queries
        if any(w in q for w in ["warranty", "warranties", "guarantee", "covered", "coverage", "expire", "expiring", "expired"]):
            return "warranty"

        # Maintenance queries
        if any(w in q for w in ["maintenance", "clean", "care", "service due", "routine check", "service schedule"]):
            return "maintenance"

        # Service / Repair queries
        if any(w in q for w in ["repair", "service history", "service center", "technician", "defect", "broken", "issue"]):
            return "service"

        # Document / Invoice queries
        if any(w in q for w in ["bill", "invoice", "receipt", "document", "pdf", "warranty card", "paperwork"]):
            return "documents"

        # Count / Summary queries
        if any(w in q for w in ["how many", "count", "summary", "overview", "all products", "list my", "what do i own", "portfolio"]):
            return "count_summary"

        return "general"


class AIRetrievalService:
    """
    Targeted context retriever for Global and Product AI Assistant modes.
    Enforces strict user isolation and produces deterministic summaries.
    """

    @property
    def products_collection(self):
        return db_manager.get_collection("products")

    @property
    def warranties_collection(self):
        return db_manager.get_collection("warranties")

    @property
    def documents_collection(self):
        return db_manager.get_collection("documents")

    @property
    def maintenance_collection(self):
        return db_manager.get_collection("maintenance_records")

    @property
    def service_records_collection(self):
        return db_manager.get_collection("service_records")

    @property
    def notifications_collection(self):
        return db_manager.get_collection("notifications")

    async def get_global_portfolio_stats(self, user_id: str) -> Dict[str, Any]:
        """
        Computes deterministic, accurate counts and summaries across user's entire portfolio.
        """
        # Fetch all user products
        prod_cursor = self.products_collection.find({"userId": user_id})
        products = [p async for p in prod_cursor]

        # Fetch all user warranties
        warr_cursor = self.warranties_collection.find({"userId": user_id})
        warranties = [w async for w in warr_cursor]

        # Fetch all user documents
        doc_cursor = self.documents_collection.find({"userId": user_id})
        documents = [d async for d in doc_cursor]

        # Fetch user maintenance records
        maint_cursor = self.maintenance_collection.find({"userId": user_id})
        maintenance_records = [m async for m in maint_cursor]

        # Fetch user service records
        srv_cursor = self.service_records_collection.find({"userId": user_id})
        service_records = [s async for s in srv_cursor]

        now = datetime.now(timezone.utc)
        today_str = now.strftime("%Y-%m-%d")

        # Analyze warranties
        active_warranties = []
        expiring_soon_warranties = []
        expired_warranties = []

        for w in warranties:
            exp_date_str = w.get("expiryDate", "")
            status = w.get("status", "Active")
            days_rem = w.get("daysRemaining", None)

            # Recalculate days remaining if possible
            if exp_date_str:
                try:
                    exp_dt = datetime.strptime(exp_date_str, "%Y-%m-%d").replace(tzinfo=timezone.utc)
                    calc_days = (exp_dt - now).days
                    if days_rem is None:
                        days_rem = calc_days
                except Exception:
                    pass

            item = {
                "id": str(w.get("_id", "")),
                "productId": w.get("productId", ""),
                "type": w.get("type", "Warranty"),
                "provider": w.get("provider", "Manufacturer"),
                "expiryDate": exp_date_str,
                "status": status,
                "daysRemaining": days_rem,
                "benefits": w.get("benefits", []),
                "exclusions": w.get("exclusions", [])
            }

            if days_rem is not None and days_rem < 0:
                expired_warranties.append(item)
            elif days_rem is not None and 0 <= days_rem <= 30:
                expiring_soon_warranties.append(item)
            else:
                active_warranties.append(item)

        # Match product names to warranties
        prod_map = {str(p["_id"]): p.get("name", "Product") for p in products}
        prod_brand_map = {str(p["_id"]): p.get("brand", "") for p in products}

        for w in active_warranties + expiring_soon_warranties + expired_warranties:
            pid = w.get("productId", "")
            w["productName"] = prod_map.get(pid, "Unknown Product")
            w["productBrand"] = prod_brand_map.get(pid, "")

        # Analyze return eligible products
        return_eligible_products = []
        for p in products:
            ret_deadline = p.get("returnDeadline")
            ret_status = p.get("returnStatus", "Expired")
            if ret_status == "Active" or (ret_deadline and ret_deadline >= today_str):
                return_eligible_products.append({
                    "id": str(p["_id"]),
                    "name": p.get("name", ""),
                    "brand": p.get("brand", ""),
                    "returnDeadline": ret_deadline,
                    "returnDuration": p.get("returnDuration", ""),
                    "seller": p.get("seller", "")
                })

        # Calculate life scores
        products_with_score = []
        for p in products:
            score = p.get("lifeScore", 80)
            products_with_score.append({
                "id": str(p["_id"]),
                "name": p.get("name", ""),
                "brand": p.get("brand", ""),
                "lifeScore": score,
                "category": p.get("category", "")
            })

        products_with_score.sort(key=lambda x: x["lifeScore"])
        lowest_life_score_products = products_with_score[:3] if products_with_score else []
        highest_life_score_products = list(reversed(products_with_score[-3:])) if products_with_score else []

        total_value = sum(float(p.get("price", 0) or 0) for p in products)

        return {
            "totalProducts": len(products),
            "totalValue": total_value,
            "totalWarranties": len(warranties),
            "activeWarrantiesCount": len(active_warranties) + len(expiring_soon_warranties),
            "expiringSoonWarrantiesCount": len(expiring_soon_warranties),
            "expiredWarrantiesCount": len(expired_warranties),
            "activeWarranties": active_warranties,
            "expiringSoonWarranties": expiring_soon_warranties,
            "expiredWarranties": expired_warranties,
            "returnEligibleProducts": return_eligible_products,
            "totalDocuments": len(documents),
            "totalMaintenanceRecords": len(maintenance_records),
            "totalServiceRecords": len(service_records),
            "lowestLifeScoreProducts": lowest_life_score_products,
            "highestLifeScoreProducts": highest_life_score_products,
            "products": [{
                "id": str(p["_id"]),
                "name": p.get("name", ""),
                "brand": p.get("brand", ""),
                "model": p.get("model", ""),
                "category": p.get("category", ""),
                "purchaseDate": p.get("purchaseDate", ""),
                "price": p.get("price", 0),
                "seller": p.get("seller", ""),
                "lifeScore": p.get("lifeScore", 80),
                "returnStatus": p.get("returnStatus", "Expired")
            } for p in products]
        }

    async def get_product_context_data(self, product_id: str, user_id: str) -> Dict[str, Any]:
        """
        Gathers complete product context for a single product owned by user_id.
        """
        from bson import ObjectId
        try:
            prod_oid = ObjectId(product_id)
        except Exception:
            prod_oid = None

        query = {"$or": [{"_id": prod_oid}, {"_id": product_id}], "userId": user_id} if prod_oid else {"_id": product_id, "userId": user_id}
        product = await self.products_collection.find_one(query)
        if not product:
            return {}

        warr_cursor = self.warranties_collection.find({"productId": product_id, "userId": user_id})
        warranties = [w async for w in warr_cursor]

        doc_cursor = self.documents_collection.find({"productId": product_id, "userId": user_id})
        documents = [d async for d in doc_cursor]

        maint_cursor = self.maintenance_collection.find({"productId": product_id, "userId": user_id})
        maintenance_records = [m async for m in maint_cursor]

        srv_cursor = self.service_records_collection.find({"productId": product_id, "userId": user_id})
        service_records = [s async for s in srv_cursor]

        return {
            "product": product,
            "warranties": warranties,
            "documents": documents,
            "maintenanceRecords": maintenance_records,
            "serviceRecords": service_records
        }


retrieval_service = AIRetrievalService()
