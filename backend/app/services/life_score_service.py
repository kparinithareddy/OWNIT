import logging
from datetime import datetime, timezone, date
from typing import List, Dict, Any, Optional
from bson import ObjectId

from app.core.database import db_manager
from app.schemas.product import ProductResponse
from app.schemas.warranty import WarrantyResponse
from app.schemas.life_score import LifeScoreResponse, LifeScoreFactor, ScoreGradeType
from app.services.product_service import product_service
from app.services.warranty_service import warranty_service

logger = logging.getLogger("ownit.services.life_score")


def calculate_age_in_days(purchase_date_str: str) -> int:
    """Calculates age in days since purchase date."""
    try:
        p_date = datetime.strptime(purchase_date_str[:10], "%Y-%m-%d").date()
        today = datetime.now(timezone.utc).date()
        diff = (today - p_date).days
        return max(0, diff)
    except Exception:
        return 0


class LifeScoreService:
    """
    Transparent, rule-based Product Life Score (0-100) engine.
    
    Evaluates:
    1. Warranty & Protection Status (Max 30 pts)
    2. Document Completeness (Max 20 pts)
    3. Maintenance & Service Care (Max 20 pts)
    4. Product Age & Lifecycle Stage (Max 15 pts)
    5. Operational Records & Identifiers (Max 15 pts)
    """

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
    def events_collection(self):
        return db_manager.get_collection("lifecycle_events")

    async def calculate_life_score(self, product_id: str, user_id: str) -> LifeScoreResponse:
        """
        Calculates a fully explainable, transparent life score based on real database records.
        """
        # 1. Fetch Product
        product = await product_service.get_product_by_id(product_id, user_id)

        # 2. Fetch Warranties
        warranties = await warranty_service.get_warranties_by_product(product_id, user_id)

        # 3. Fetch Documents
        doc_cursor = self.documents_collection.find({"productId": product_id, "userId": user_id})
        documents = [doc async for doc in doc_cursor]

        # 4. Fetch Maintenance Records
        maint_cursor = self.maintenance_collection.find({"productId": product_id, "userId": user_id})
        maintenance_records = [m async for m in maint_cursor]

        # 5. Fetch Service History Records
        service_records = []
        if self.service_records_collection is not None:
            srv_cursor = self.service_records_collection.find({"productId": product_id, "userId": user_id})
            service_records = [s async for s in srv_cursor]

        # 6. Fetch Custom Lifecycle Events
        events_cursor = self.events_collection.find({"productId": product_id, "userId": user_id})
        custom_events = [e async for e in events_cursor]

        return self.compute_score(
            product=product,
            warranties=warranties,
            documents=documents,
            maintenance_records=maintenance_records,
            service_records=service_records,
            custom_events=custom_events
        )

    def compute_score(
        self,
        product: ProductResponse,
        warranties: List[WarrantyResponse],
        documents: List[Dict[str, Any]],
        maintenance_records: List[Dict[str, Any]],
        service_records: Optional[List[Dict[str, Any]]] = None,
        custom_events: Optional[List[Dict[str, Any]]] = None
    ) -> LifeScoreResponse:
        factors: List[LifeScoreFactor] = []
        positive_reasons: List[str] = []
        improvement_tips: List[str] = []

        total_score = 0

        # -------------------------------------------------------------
        # Factor 1: Warranty & Coverage Status (Max 30 pts)
        # -------------------------------------------------------------
        w_max = 30
        w_score = 0
        w_status = "negative"
        w_desc = "No active warranty coverage recorded."

        has_active_warranty = any(w.status == "Active" for w in warranties)
        has_expiring_soon = any(w.status == "Expiring Soon" for w in warranties)
        all_expired = len(warranties) > 0 and all(w.status == "Expired" for w in warranties)

        if has_active_warranty:
            # Active warranty with multi-component coverage
            active_count = sum(1 for w in warranties if w.status == "Active")
            w_score = 30 if active_count > 1 else 26
            w_status = "positive"
            w_desc = f"{active_count} active warranty component(s) protecting the asset."
            positive_reasons.append(f"Active warranty coverage in good standing ({active_count} tier(s))")
        elif has_expiring_soon:
            w_score = 15
            w_status = "warning"
            w_desc = "Warranty coverage is expiring soon (within 30 days)."
            positive_reasons.append("Warranty is currently active but nearing expiration")
            improvement_tips.append("Consider purchasing an extended warranty before the current period expires")
        elif all_expired:
            w_score = 6
            w_status = "negative"
            w_desc = "All registered warranty components have expired."
            improvement_tips.append("Explore third-party extended warranty or service plans for continued protection")
        else:
            w_score = 0
            w_status = "negative"
            w_desc = "No warranty details registered for this product."
            improvement_tips.append("Add your manufacturer warranty or extended protection details")

        total_score += w_score
        factors.append(LifeScoreFactor(
            name="Warranty & Coverage",
            score=w_score,
            maxScore=w_max,
            status=w_status,
            description=w_desc,
            details=f"{len(warranties)} registered component(s)"
        ))

        # -------------------------------------------------------------
        # Factor 2: Document Completeness (Max 20 pts)
        # -------------------------------------------------------------
        doc_max = 20
        doc_score = 0
        doc_types = {d.get("documentType") for d in documents}

        has_bill = "Purchase Bill" in doc_types
        has_warranty_card = "Warranty Card" in doc_types or "Extended Warranty" in doc_types
        has_manual = "User Manual" in doc_types
        has_service_invoice = "Service Invoice" in doc_types

        if has_bill:
            doc_score += 10
            positive_reasons.append("Original Purchase Bill attached for proof of purchase")
        else:
            improvement_tips.append("Attach the Purchase Bill / Invoice to preserve warranty claim proof")

        if has_warranty_card:
            doc_score += 5
            positive_reasons.append("Warranty Card / Certificate uploaded")
        
        if has_manual or has_service_invoice or len(documents) >= 2:
            doc_score += 5
            positive_reasons.append("Supplemental documentation (manual/invoice) attached")

        doc_score = min(doc_max, doc_score)
        
        if doc_score >= 15:
            doc_status = "positive"
            doc_desc = "Comprehensive documentation stored for this asset."
        elif doc_score >= 8:
            doc_status = "warning"
            doc_desc = "Essential purchase bill attached; other documents missing."
        else:
            doc_status = "negative"
            doc_desc = "Missing proof of purchase or warranty paperwork."

        total_score += doc_score
        factors.append(LifeScoreFactor(
            name="Document Completeness",
            score=doc_score,
            maxScore=doc_max,
            status=doc_status,
            description=doc_desc,
            details=f"{len(documents)} document(s) attached"
        ))

        # -------------------------------------------------------------
        # Factor 3: Maintenance & Service Health (Max 20 pts)
        # -------------------------------------------------------------
        maint_max = 20
        maint_score = 0
        
        completed_maint = [m for m in maintenance_records if m.get("status") == "Completed"]
        overdue_maint = [m for m in maintenance_records if m.get("status") == "Overdue"]
        scheduled_maint = [m for m in maintenance_records if m.get("status") == "Scheduled"]

        if len(overdue_maint) > 0:
            maint_score = 0
            maint_status = "negative"
            maint_desc = f"{len(overdue_maint)} maintenance action(s) currently overdue!"
            improvement_tips.append("Complete and log overdue maintenance tasks to prevent degradation")
        elif len(completed_maint) >= 2:
            maint_score = 20
            maint_status = "positive"
            maint_desc = f"Consistent service history with {len(completed_maint)} completed maintenance record(s)."
            positive_reasons.append(f"Regular maintenance routine maintained ({len(completed_maint)} logs)")
        elif len(completed_maint) == 1:
            maint_score = 16
            maint_status = "positive"
            maint_desc = "Initial maintenance record logged."
            positive_reasons.append("Active maintenance care recorded")
        elif len(scheduled_maint) > 0:
            maint_score = 12
            maint_status = "warning"
            maint_desc = f"{len(scheduled_maint)} maintenance action(s) scheduled."
            positive_reasons.append("Upcoming maintenance service scheduled")
        else:
            # If product is very new (< 90 days), grant partial baseline points
            age_days = calculate_age_in_days(product.purchaseDate)
            if age_days < 90:
                maint_score = 12
                maint_status = "positive"
                maint_desc = "Asset is newly acquired; routine maintenance not yet due."
            else:
                maint_score = 6
                maint_status = "warning"
                maint_desc = "No maintenance, cleaning, or routine servicing logged yet."
                improvement_tips.append("Log periodic maintenance, cleaning, or inspections to sustain asset value")

        # Supplement with professional service / repair history records
        if service_records and len(service_records) > 0:
            srv_count = len(service_records)
            maint_score = min(maint_max, maint_score + min(8, srv_count * 4))
            if maint_score >= 15:
                maint_status = "positive"
            maint_desc += f" Verified service history logged ({srv_count} repair/service record(s))."
            positive_reasons.append(f"Professional service & repair history recorded ({srv_count} record(s))")

        total_score += maint_score
        factors.append(LifeScoreFactor(
            name="Maintenance & Care",
            score=maint_score,
            maxScore=maint_max,
            status=maint_status,
            description=maint_desc,
            details=f"{len(completed_maint)} maintenance, {len(service_records or [])} service logs"
        ))

        # -------------------------------------------------------------
        # Factor 4: Product Age & Lifecycle Stage (Max 15 pts)
        # -------------------------------------------------------------
        age_max = 15
        age_days = calculate_age_in_days(product.purchaseDate)
        age_years = age_days / 365.25

        if age_years < 1.0:
            age_score = 15
            age_status = "positive"
            age_desc = f"New asset lifecycle stage ({age_days} days old)."
            positive_reasons.append("Asset is in its early prime lifecycle stage (< 1 year)")
        elif age_years < 3.0:
            age_score = 12
            age_status = "positive"
            age_desc = f"Mature lifecycle stage ({age_years:.1f} years old)."
            positive_reasons.append("Asset is in healthy active lifecycle stage (1–3 years)")
        elif age_years < 5.0:
            age_score = 8
            age_status = "warning"
            age_desc = f"Mid-life lifecycle stage ({age_years:.1f} years old)."
        else:
            age_score = 4
            age_status = "warning"
            age_desc = f"Extended lifecycle stage ({age_years:.1f} years old)."

        total_score += age_score
        factors.append(LifeScoreFactor(
            name="Product Age",
            score=age_score,
            maxScore=age_max,
            status=age_status,
            description=age_desc,
            details=f"Purchased: {product.purchaseDate}"
        ))

        # -------------------------------------------------------------
        # Factor 5: Operational Records & Identifiers (Max 15 pts)
        # -------------------------------------------------------------
        ident_max = 15
        ident_score = 0

        has_serial = bool(product.serialNumber and product.serialNumber.strip())
        has_imei = bool(product.imei and product.imei.strip())
        has_seller = bool(product.seller and product.seller.strip())
        has_verified_return = product.returnStatus in ["Active", "Ending Soon", "Expired"]

        if has_serial:
            ident_score += 6
            positive_reasons.append("Hardware Serial Number recorded for asset verification")
        else:
            improvement_tips.append("Add the device serial number for quick warranty claims")

        if has_imei:
            ident_score += 3
            positive_reasons.append("Cellular IMEI number registered")

        if has_seller:
            ident_score += 3

        if has_verified_return:
            ident_score += 3

        ident_score = min(ident_max, ident_score)
        ident_status = "positive" if ident_score >= 10 else ("warning" if ident_score >= 6 else "negative")
        ident_desc = "Essential hardware identification and seller records are documented." if ident_score >= 10 else "Missing key hardware identification (e.g. Serial #)."

        total_score += ident_score
        factors.append(LifeScoreFactor(
            name="Asset Identifiers & Records",
            score=ident_score,
            maxScore=ident_max,
            status=ident_status,
            description=ident_desc,
            details="Serial # & Seller verification"
        ))

        # -------------------------------------------------------------
        # Total Score Normalization & Grading (0–100)
        # -------------------------------------------------------------
        total_score = max(0, min(100, total_score))

        if total_score >= 90:
            grade: ScoreGradeType = "Excellent"
            color = "green"
            summary = "Asset has optimal warranty coverage, complete documentation, and healthy maintenance records."
        elif total_score >= 75:
            grade = "Good"
            color = "green"
            summary = "Asset is in good overall health with solid protection and verified details."
        elif total_score >= 50:
            grade = "Fair"
            color = "amber"
            summary = "Asset has moderate documentation or coverage, with noticeable areas for improvement."
        else:
            grade = "Needs Attention"
            color = "red"
            summary = "Asset requires attention: missing critical warranties, documentation, or has overdue maintenance."

        return LifeScoreResponse(
            productId=product.id,
            score=total_score,
            grade=grade,
            color=color,
            summary=summary,
            disclaimer="This rule-based score evaluates ownership completeness and maintenance health. It is not a scientifically predictive model of hardware failure.",
            factors=factors,
            positiveReasons=positive_reasons,
            improvementTips=improvement_tips,
            calculatedAt=datetime.now(timezone.utc)
        )


life_score_service = LifeScoreService()
