import pytest
import uuid
import os
import io
from datetime import datetime, timezone, timedelta
from fastapi import UploadFile

from bson import ObjectId
from app.core.database import db_manager
from app.schemas.user import UserSignupRequest, UserLoginRequest, UserPreferencesUpdate
from app.schemas.product import ProductCreate, ProductUpdate
from app.schemas.warranty import WarrantyCreate
from app.schemas.maintenance import MaintenanceCreate
from app.schemas.service_history import ServiceRecordCreate
from app.schemas.ocr import OCRConfirmRequest, OCRConfirmItem
from app.schemas.warranty_intelligence import WarrantyQuestionRequest, WarrantyIntelligenceResponse, CoverageLikelihood
from app.schemas.claim_assistant import ClaimPreparationRequest, ClaimPreparationResponse
from app.services.user_service import user_service
from app.services.product_service import product_service
from app.services.warranty_service import warranty_service, calculate_expiry_date, calculate_warranty_status
from app.services.document_service import document_service
from app.services.ocr_service import ReceiptParser, ocr_service
from app.services.notification_service import notification_service
from app.services.timeline_service import timeline_service
from app.services.maintenance_service import maintenance_service
from app.services.life_score_service import life_score_service
from app.services.ai_service import ai_service
from app.services.context_builder import build_product_system_context
from app.services.warranty_intelligence_service import warranty_intelligence_service
from app.services.claim_assistant_service import claim_assistant_service
from app.services.service_history_service import service_history_service
from app.services.accessory_service import accessory_service
from app.services.recall_service import recall_service


@pytest.mark.anyio
async def test_complete_26_step_user_journey():
    """
    Comprehensive End-to-End integration test validating the entire 26-step user journey:
    1. Signup -> 2. Login -> 3. Dashboard -> 4. Scan Receipt -> 5. OCR -> 6. Detect Multiple Products
    -> 7. Confirm/Edit -> 8. Save Products -> 9. Upload Document -> 10. Extract Warranty
    -> 11. Confirm Warranty -> 12. Expiry Calc -> 13. Warranty Status -> 14. Reminders
    -> 15. Lifecycle Timeline -> 16. Maintenance -> 17. Product Life Score -> 18. Product AI
    -> 19. Ask Product Question -> 20. Ask Warranty Question -> 21. Problem Coverage
    -> 22. Prepare Claim -> 23. Service History -> 24. Change Language -> 25. Accessories
    -> 26. Safety/Recall Alerts
    """
    if not db_manager.is_connected:
        is_conn = await db_manager.connect()
        if not is_conn:
            pytest.skip("MongoDB service is offline in the test environment.")

    unique_suffix = uuid.uuid4().hex[:8]
    test_username = f"user_{unique_suffix}"
    test_password = "SecurePassword123!"

    # Step 1: Signup
    signup_data = UserSignupRequest(
        username=test_username,
        password=test_password,
        confirmPassword=test_password,
        preferredLanguage="en"
    )
    signup_res = await user_service.signup(signup_data)
    assert signup_res.accessToken is not None
    assert signup_res.user.username == test_username
    user_id = signup_res.user.id

    # Step 2: Login
    login_result = await user_service.login(UserLoginRequest(username=test_username, password=test_password))
    assert login_result.accessToken is not None
    assert login_result.user.id == user_id

    # Step 3: Dashboard Overview (Initial Zero State)
    initial_products = await product_service.get_user_products(user_id)
    initial_w_summary = await warranty_service.get_warranty_summary(user_id)
    initial_recalls = await recall_service.scan_user_vault(user_id)
    assert initial_products == []
    assert initial_w_summary.totalWarranties == 0
    assert initial_recalls.alertsCount == 0

    # Step 4 & 5: Scan Receipt & OCR Extraction
    sample_invoice_text = """
    RELIANCE DIGITAL RETAIL LTD
    Tax Invoice: INV-2025-00918
    Date: 2025-01-15

    1. Samsung 55 Inch 4K Smart TV UA55DU8000
       Qty: 1   Price: 54,990.00
       Serial: SAMSUNG-TV-991823

    2. Sony WH-1000XM5 Wireless Noise Cancelling Headphones
       Qty: 1   Price: 26,990.00
       Serial: SONY-WH-776655

    Warranty: 1 Year Comprehensive Manufacturer Warranty
    Total Amount: INR 81,980.00
    """
    candidate_items, receipt_meta = ReceiptParser.parse_receipt(sample_invoice_text)

    # Step 6: Detect Multiple Products
    assert len(candidate_items) >= 2
    tv_candidate = next((it for it in candidate_items if "Samsung" in it.name or "TV" in it.name), None)
    audio_candidate = next((it for it in candidate_items if "Sony" in it.name or "Headphones" in it.name), None)
    assert tv_candidate is not None
    assert audio_candidate is not None

    # Step 7: Confirm / Edit Products
    tv_candidate.category = "TV"
    tv_candidate.seller = "Reliance Digital"
    audio_candidate.category = "Audio"
    audio_candidate.seller = "Reliance Digital"

    # Step 8: Save Products into Vault
    confirm_payload = OCRConfirmRequest(
        items=[
            OCRConfirmItem(
                name=tv_candidate.name,
                brand="Samsung",
                model="UA55DU8000",
                category="TV",
                purchaseDate="2025-01-15",
                price=54990.0,
                quantity=1,
                seller="Reliance Digital",
                serialNumber="SAMSUNG-TV-991823"
            ),
            OCRConfirmItem(
                name=audio_candidate.name,
                brand="Sony",
                model="WH-1000XM5",
                category="Audio",
                purchaseDate="2025-01-15",
                price=26990.0,
                quantity=1,
                seller="Reliance Digital",
                serialNumber="SONY-WH-776655"
            )
        ],
        documentType="Purchase Bill"
    )
    save_res = await ocr_service.confirm_and_save(user_id=user_id, payload=confirm_payload)
    assert len(save_res.createdProducts) == 2
    tv_product = save_res.createdProducts[0]
    audio_product = save_res.createdProducts[1]
    assert tv_product.userId == user_id
    assert audio_product.userId == user_id

    # Step 9: Upload Warranty Document
    dummy_pdf_bytes = b"%PDF-1.4\n1 0 obj<</Type/Catalog/Pages 2 0 R>>endobj\nxref\n0 2\ntrailer<</Size 2/Root 1 0 R>>\nstartxref\n50\n%%EOF"
    upload_file = UploadFile(
        file=io.BytesIO(dummy_pdf_bytes),
        filename="Samsung_TV_Warranty.pdf",
        headers={"content-type": "application/pdf"}
    )
    doc_res = await document_service.upload_document(
        user_id=user_id,
        product_id=tv_product.id,
        document_type="Warranty Card",
        file=upload_file
    )
    assert doc_res.id is not None
    assert doc_res.productId == tv_product.id

    # Step 10 & 11: Extract Warranty & Confirm Multi-Tier Components
    w_comp = await warranty_service.create_warranty(
        user_id=user_id,
        data=WarrantyCreate(
            productId=tv_product.id,
            provider="Samsung India",
            type="Comprehensive",
            startDate="2025-01-15",
            duration="12 Months",
            benefits="Panel Coverage, Mainboard Replacement, In-Home Technician Visit"
        )
    )
    w_panel = await warranty_service.create_warranty(
        user_id=user_id,
        data=WarrantyCreate(
            productId=tv_product.id,
            provider="Samsung Care+",
            type="Panel Warranty",
            startDate="2025-01-15",
            duration="120 Months",
            benefits="Display Panel Defects, Zero Bright Dot Guarantee"
        )
    )
    assert w_comp.id is not None
    assert w_panel.id is not None

    # Step 12: Calculate Expiry
    calc_exp_date = calculate_expiry_date("2025-01-15", "12 months")
    assert calc_exp_date == "2026-01-15"

    # Step 13: Display Warranty Status
    w_list = await warranty_service.get_warranties_by_product(tv_product.id, user_id)
    assert len(w_list) == 2
    assert any(w.type == "Comprehensive" for w in w_list)
    assert any(w.type == "Panel Warranty" for w in w_list)

    # Step 14: Generate Reminders
    notifs = await notification_service.evaluate_warranty_reminders(user_id=user_id)
    unread_count = await notification_service.get_unread_count(user_id)
    assert unread_count >= 0

    # Step 15: View Lifecycle Timeline
    timeline = await timeline_service.get_product_timeline(tv_product.id, user_id)
    assert timeline.productId == tv_product.id
    assert len(timeline.events) >= 1
    event_types = [e.eventType.lower() for e in timeline.events]
    assert any("purchase" in et for et in event_types)

    # Step 16: Add Maintenance & Get Recommendations
    maint_recs = await maintenance_service.get_recommendations_for_product(tv_product.id, user_id)
    assert len(maint_recs) > 0

    maint_entry = await maintenance_service.create_record(
        user_id=user_id,
        data=MaintenanceCreate(
            productId=tv_product.id,
            title="Clean Screen & Dust Vents",
            type="Cleaning",
            date="2025-02-01",
            status="Completed",
            notes="Wiped with microfiber cloth, inspected heat vents"
        )
    )
    assert maint_entry.id is not None

    # Step 17: View Product Life Score
    score_res = await life_score_service.calculate_life_score(tv_product.id, user_id)
    assert 0 <= score_res.score <= 100
    assert score_res.grade in ["Excellent", "Good", "Fair", "Needs Attention"]
    assert len(score_res.factors) == 5
    assert len(score_res.positiveReasons) > 0

    # Step 18: Open Product-Specific AI & Check Status
    ai_stat = await ai_service.check_health()
    assert ai_stat.provider == "Ollama"

    # Step 19 & 20: Ask Product & Warranty Questions
    ai_context, sources = build_product_system_context(
        product=tv_product,
        warranties=w_list,
        documents=[{"documentType": "Warranty Card", "originalFilename": "Samsung_TV_Warranty.pdf"}],
        maintenance_records=[{"title": "Clean Screen"}],
        recommendations=[{"title": "General Inspection"}],
        language="en"
    )
    assert "UA55DU8000" in ai_context
    assert "Samsung" in ai_context
    assert "PROMPT INJECTION DEFENSE" in ai_context
    assert len(sources) > 0

    # Step 21: Check Problem Coverage
    defect_check = await warranty_intelligence_service.analyze_issue_or_question(
        user_id=user_id,
        request=WarrantyQuestionRequest(
            productId=tv_product.id,
            issueDescription="Screen display has horizontal flickering lines and color distortion without physical impact."
        )
    )
    assert defect_check.coverageLikelihood in [CoverageLikelihood.CONFIRMED, CoverageLikelihood.LIKELY, CoverageLikelihood.UNCLEAR]
    assert len(defect_check.recommendedAction) > 0

    # Step 22: Prepare Warranty Claim Dossier
    claim_dossier = await claim_assistant_service.prepare_claim_dossier(
        user_id=user_id,
        request=ClaimPreparationRequest(
            productId=tv_product.id,
            problemDescription="Display has green flickering lines appearing during normal use.",
            problemStartDate="2025-02-10",
            incidentDetails="Television is wall mounted; cables reseated and factory reset attempted."
        )
    )
    assert claim_dossier.productName == tv_product.name
    assert len(claim_dossier.draftSupportMessage) > 50
    assert len(claim_dossier.confirmationChecklist) > 0

    # Step 23: View & Log Service History
    service_rec = await service_history_service.create_service_record(
        user_id=user_id,
        data=ServiceRecordCreate(
            productId=tv_product.id,
            serviceDate="2025-02-15",
            problem="HDMI Port 2 loose connection",
            serviceCenter="Samsung Authorized Plaza",
            workPerformed="Replaced HDMI daughterboard connector",
            cost=0.0,
            warrantyCovered=True,
            notes="Repaired under manufacturer warranty"
        )
    )
    assert service_rec.id is not None
    user_services = await service_history_service.get_service_records_by_product(tv_product.id, user_id)
    assert len(user_services) == 1

    # Step 24: Change Language
    pref_res = await user_service.update_preferences(
        user_id=user_id,
        prefs=UserPreferencesUpdate(preferredLanguage="hi")
    )
    assert pref_res.preferredLanguage == "hi"

    # Step 25: Find Compatible Accessories
    acc_res = await accessory_service.get_product_recommendations(
        user_id=user_id,
        product_id=tv_product.id,
        min_budget=1000.0,
        max_budget=10000.0
    )
    assert len(acc_res.recommendations) > 0
    categories = [a.category.lower() for a in acc_res.recommendations]
    assert any(c in ["wall mount", "soundbar", "hdmi cable", "surge protector"] for c in categories)

    # Step 26: View Safety / Recall Alerts
    recall_res = await recall_service.check_product(user_id=user_id, product_id=tv_product.id)
    assert recall_res.productId == tv_product.id
    assert recall_res.hasPossibleRecall is False

    # Clean up test user records
    await product_service.collection.delete_many({"userId": user_id})
    await product_service.db["warranties"].delete_many({"userId": user_id})
    await product_service.db["documents"].delete_many({"userId": user_id})
    await product_service.db["maintenance_records"].delete_many({"userId": user_id})
    await product_service.db["service_records"].delete_many({"userId": user_id})
    await product_service.db["notifications"].delete_many({"userId": user_id})
    await user_service.users_collection.delete_many({"_id": ObjectId(user_id)})
