import pytest
import uuid
from datetime import datetime, timezone, timedelta, date
from app.schemas.product import ProductCreate, ProductResponse
from app.schemas.warranty import WarrantyCreate, WarrantyResponse
from app.schemas.document import DocumentResponse
from app.schemas.maintenance import MaintenanceCreate
from app.services.product_service import product_service, format_product_doc
from app.services.warranty_service import (
    warranty_service,
    calculate_warranty_status,
    calculate_expiry_date
)
from app.services.document_service import document_service, validate_magic_bytes
from app.services.life_score_service import life_score_service
from app.services.ocr_service import ReceiptParser
from app.services.product_extractor import extraction_manager
from app.services.recall_service import recall_service
from app.services.ai_service import OllamaAIService
from app.services.context_builder import build_product_system_context
from app.core.exceptions import ValidationException, NotFoundException, AppException
from app.core.database import db_manager


# ---------------------------------------------------------------------------
# 1. Edge Case: Empty Database & Zero-Item Fallbacks
# ---------------------------------------------------------------------------
@pytest.mark.anyio
async def test_empty_user_vault_fallbacks():
    empty_user = f"empty_user_{uuid.uuid4().hex[:8]}"

    # Product list on empty user
    if db_manager.is_connected:
        prods = await product_service.get_user_products(empty_user)
        assert prods == []

        docs = await document_service.list_user_documents(empty_user)
        assert docs == []

        w_summary = await warranty_service.get_warranty_summary(empty_user)
        assert w_summary.totalWarranties == 0
        assert w_summary.active == 0


# ---------------------------------------------------------------------------
# 2. Edge Case: Invalid Documents & Bad Magic Bytes
# ---------------------------------------------------------------------------
def test_invalid_document_and_corrupt_files():
    # Empty file bytes
    assert validate_magic_bytes(b"", ".pdf") is False

    # Corrupt PDF (random text)
    corrupt_pdf = b"Hello World this is not a PDF file"
    assert validate_magic_bytes(corrupt_pdf, ".pdf") is False

    # Fake JPEG (HTML file renamed .jpg)
    fake_jpg = b"<html><head><title>Test</title></head></html>"
    assert validate_magic_bytes(fake_jpg, ".jpg") is False

    # Valid PNG
    valid_png = b"\x89PNG\r\n\x1a\n\x00\x00\x00\rIHDR"
    assert validate_magic_bytes(valid_png, ".png") is True


# ---------------------------------------------------------------------------
# 3. Edge Case: Poor / Blurry / Gibberish OCR Parsing
# ---------------------------------------------------------------------------
def test_poor_and_gibberish_ocr_handling():
    # Unintelligible noise
    gibberish_text = "%$^&*#@ )(*&^% \n ~~~ \n ??? 000"
    items, meta = ReceiptParser.parse_receipt(gibberish_text)
    
    # Should not crash, should produce low confidence fallback
    assert len(items) >= 1
    for item in items:
        assert item.confidence <= 0.6
        assert item.confidenceLevel in ["medium", "low"]

    # Empty text
    empty_items, empty_meta = ReceiptParser.parse_receipt("")
    assert len(empty_items) == 1
    assert empty_items[0].confidenceLevel == "low"
    assert empty_meta["totalAmount"] is None


# ---------------------------------------------------------------------------
# 4. Edge Case: Multiple-Product Receipts
# ---------------------------------------------------------------------------
def test_multiple_product_receipt_extraction():
    multi_receipt_text = """
    RELIANCE DIGITAL RETAIL LTD
    Tax Invoice / Bill of Supply
    Date: 2025-06-15

    1. Apple iPhone 15 128GB Black
       Qty: 1   Rate: 69,900.00   Amount: 69,900.00
       Serial: F4KZX999ABCD

    2. Sony WH-1000XM5 Wireless Headphones
       Qty: 1   Rate: 26,990.00   Amount: 26,990.00
       Serial: SONY-WH-887766

    3. Belkin 65W GaN Dual USB-C Charger
       Qty: 1   Rate: 3,499.00    Amount: 3,499.00

    Total Items: 3
    Grand Total: INR 1,00,389.00
    """
    items, meta = ReceiptParser.parse_receipt(multi_receipt_text)
    assert len(items) >= 2
    
    names = [it.name for it in items]
    assert any("iPhone" in n for n in names)
    assert any("Sony" in n or "Headphones" in n for n in names)


# ---------------------------------------------------------------------------
# 5. Edge Case: Multiple Warranties & Expiration Calculations
# ---------------------------------------------------------------------------
def test_multiple_warranties_and_expiry_calculations():
    today = datetime.now(timezone.utc).date()
    today_str = today.isoformat()

    # Expired 100 days ago
    expired_date = (today - timedelta(days=100)).isoformat()
    status_exp, days_exp, color_exp = calculate_warranty_status(expired_date)
    assert status_exp == "Expired"
    assert days_exp == -100
    assert color_exp == "red"

    # Expiring soon (10 days remaining)
    soon_date = (today + timedelta(days=10)).isoformat()
    status_soon, days_soon, color_soon = calculate_warranty_status(soon_date)
    assert status_soon == "Expiring Soon"
    assert days_soon == 10
    assert color_soon == "amber"

    # Active (> 30 days, e.g. 180 days)
    active_date = (today + timedelta(days=180)).isoformat()
    status_act, days_act, color_act = calculate_warranty_status(active_date)
    assert status_act == "Active"
    assert days_act == 180
    assert color_act == "green"


# ---------------------------------------------------------------------------
# 6. Edge Case: Missing Model, Missing Serial Number, Missing Warranty
# ---------------------------------------------------------------------------
def test_missing_model_serial_warranty_in_life_score():
    # Product with minimal fields (no model, no serial number, no warranties)
    minimal_product = ProductResponse(
        id="66dbb01234abcd5678ef9111",
        userId="66dbb01234abcd5678ef9099",
        name="Desk Lamp",
        brand="Generic",
        model="",
        category="Home Appliance",
        purchaseDate="2024-01-01",
        price=1200.0,
        quantity=1,
        serialNumber=None,
        createdAt=datetime.now(timezone.utc),
        updatedAt=datetime.now(timezone.utc)
    )

    score_result = life_score_service.compute_score(
        product=minimal_product,
        warranties=[],
        documents=[],
        maintenance_records=[],
        service_records=[]
    )

    assert score_result.score >= 0
    assert score_result.score <= 100
    assert score_result.grade in ["Excellent", "Good", "Fair", "Needs Attention"]
    # Check that lack of warranty is reflected in factor score (0 out of 30)
    warranty_factor = next(f for f in score_result.factors if f.name == "Warranty & Coverage")
    assert warranty_factor.score == 0
    assert warranty_factor.status == "negative"


# ---------------------------------------------------------------------------
# 7. Edge Case: Safety Recall Check with Missing Serial vs Exact Serial
# ---------------------------------------------------------------------------
@pytest.mark.anyio
async def test_safety_recall_missing_serial_vs_exact_match():
    # Apple 15-inch MBP with NO serial number recorded
    product_no_serial = ProductResponse(
        id="66dbb01234abcd5678ef9222",
        userId="66dbb01234abcd5678ef9099",
        name="MacBook Pro",
        brand="Apple",
        model="A1398 Mid 2015",
        category="Laptop",
        purchaseDate="2016-01-01",
        price=180000.0,
        quantity=1,
        serialNumber=None,
        createdAt=datetime.now(timezone.utc),
        updatedAt=datetime.now(timezone.utc)
    )

    check_res = await recall_service.retrieval_engine.check_product_recall(product_no_serial)
    assert check_res.hasPossibleRecall is True
    assert check_res.warningMessage == "Possible recall match — verify with the official source."
    assert len(check_res.matches) > 0
    # Since user recorded no serial, isSerialMatched must be None (Prompting user to check)
    assert check_res.matches[0].isSerialMatched is None


# ---------------------------------------------------------------------------
# 8. Edge Case: AI Offline & Ollama Unreachable Handling
# ---------------------------------------------------------------------------
@pytest.mark.anyio
async def test_ollama_unavailable_graceful_handling():
    # Initialize service pointing to invalid port
    offline_ai = OllamaAIService()
    offline_ai.base_url = "http://127.0.0.1:59999"

    status = await offline_ai.check_health()
    assert status.isAvailable is False
    assert status.provider == "Ollama"

    # Test text generation when offline
    res = await offline_ai.generate_text(prompt="Hello")
    assert res.success is False
    assert "offline" in res.error.lower() or "unreachable" in res.error.lower() or "failed" in res.error.lower()


# ---------------------------------------------------------------------------
# 9. Edge Case: AI Context Builder with Incomplete Data
# ---------------------------------------------------------------------------
def test_ai_context_builder_incomplete_product():
    product_sparse = ProductResponse(
        id="66dbb01234abcd5678ef9333",
        userId="66dbb01234abcd5678ef9099",
        name="Unknown Device",
        brand="Unknown",
        model="N/A",
        category="Other",
        purchaseDate="2025-01-01",
        price=0.0,
        quantity=1,
        serialNumber=None,
        createdAt=datetime.now(timezone.utc),
        updatedAt=datetime.now(timezone.utc)
    )

    prompt, sources = build_product_system_context(
        product=product_sparse,
        warranties=[],
        documents=[],
        maintenance_records=[],
        recommendations=[],
        language="en"
    )

    assert "Unknown Device" in prompt
    assert "PROMPT INJECTION DEFENSE" in prompt
    assert len(sources) > 0
