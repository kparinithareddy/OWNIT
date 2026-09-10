import io
import pytest
import pymupdf
from PIL import Image, ImageDraw, ImageFont
from app.core.ocr_engine import OCREngine
from app.services.ocr_service import ReceiptParser, OCRService
from app.schemas.ocr import OCRExtractedItem, OCRConfirmRequest, OCRConfirmItem


def create_sample_receipt_image(text_lines):
    """Generates a synthetic receipt image for testing OCR."""
    img = Image.new("RGB", (800, 1000), color=(255, 255, 255))
    draw = ImageDraw.Draw(img)
    y = 50
    for line in text_lines:
        draw.text((50, y), line, fill=(0, 0, 0))
        y += 40
    buffer = io.BytesIO()
    img.save(buffer, format="PNG")
    return buffer.getvalue()


def create_sample_receipt_pdf(text_lines):
    """Generates a synthetic PDF receipt for testing PDF extraction."""
    doc = pymupdf.open()
    page = doc.new_page(width=595, height=842)
    p = pymupdf.Point(50, 72)
    for line in text_lines:
        page.insert_text(p, line, fontsize=12, color=(0, 0, 0))
        p.y += 24
    return doc.tobytes()


def test_receipt_parser_single_product():
    sample_text = """
    RELIANCE DIGITAL RETAIL LIMITED
    Tax Invoice / Bill of Supply
    Invoice No: RD-2024-88491
    Date: 2024-06-15
    Sold By: Reliance Digital Mumbai

    Item Description: Apple iPhone 15 Pro 128GB Blue Titanium
    Model: A3101
    Serial No: F2LL89J90X
    IMEI: 359123456789012
    Warranty: 1 Year Manufacturer Warranty

    Qty: 1
    Total Amount: INR 134,900.00
    Thank you for shopping with Reliance Digital!
    """
    items, meta = ReceiptParser.parse_receipt(sample_text)
    
    assert len(items) >= 1
    item = items[0]
    assert item.brand == "Apple"
    assert item.category == "Mobile"
    assert "iPhone 15 Pro" in item.name
    assert item.price == 134900.0
    assert item.purchaseDate == "2024-06-15"
    assert item.seller == "Reliance Digital"
    assert item.serialNumber == "F2LL89J90X"
    assert item.imei == "359123456789012"
    assert item.warrantyInfo is not None
    assert item.confidenceLevel in ("high", "medium")
    assert meta["invoiceNumber"] == "RD-2024-88491"


def test_receipt_parser_multiple_products():
    multi_item_text = """
    Croma Electronics Store
    Invoice Number: CR-99120
    Date: 12-Nov-2024
    
    1. Dell XPS 15 9530 Laptop Core i7 - INR 165,000.00
    2. Sony WH-1000XM5 Noise Cancelling Headphones - INR 26,990.00
    
    Grand Total: INR 191,990.00
    """
    items, meta = ReceiptParser.parse_receipt(multi_item_text)
    
    assert len(items) == 2
    
    # Item 1: Laptop
    laptop = items[0]
    assert laptop.brand == "Dell"
    assert laptop.category == "Laptop"
    assert laptop.price == 165000.0
    
    # Item 2: Headphones
    headphones = items[1]
    assert headphones.brand == "Sony"
    assert headphones.category == "Audio"
    assert headphones.price == 26990.0
    
    assert meta["seller"] == "Croma"
    assert meta["totalAmount"] == 191990.0


def test_receipt_parser_poor_noisy_image():
    noisy_text = """
    *** FADED STORE SLIP ***
    Txn: Unknown
    Some unreadable chars @@##$$%
    Microwave 20L
    """
    items, meta = ReceiptParser.parse_receipt(noisy_text)
    
    assert len(items) >= 1
    item = items[0]
    # Price and Date are missing, so they must be flagged in uncertainFields
    assert "price" in item.uncertainFields or item.price is None
    assert item.confidence < 0.8
    assert item.confidenceLevel in ("medium", "low")


def test_ocr_engine_with_synthetic_pdf():
    lines = [
        "Amazon India Tax Invoice",
        "Invoice Number: IN-882190",
        "Date: 2024-08-20",
        "Sold By: Amazon",
        "Samsung Galaxy S24 Ultra 256GB Titanium Gray",
        "Total Amount: ₹ 129,999.00"
    ]
    pdf_bytes = create_sample_receipt_pdf(lines)
    extracted_text, metadata = OCREngine.extract_text_from_pdf_bytes(pdf_bytes)
    
    assert "Samsung Galaxy S24 Ultra" in extracted_text
    assert "Amazon" in extracted_text
    
    items, meta = ReceiptParser.parse_receipt(extracted_text)
    assert len(items) >= 1
    assert items[0].brand == "Samsung"
    assert items[0].category == "Mobile"
    assert items[0].price == 129999.0


def test_ocr_engine_with_synthetic_image():
    if not OCREngine.is_tesseract_available():
        pytest.skip("Tesseract OCR not installed or not in PATH")
        
    lines = [
        "CROMA STORE",
        "TAX INVOICE",
        "Date: 2024-04-10",
        "Sony Bravia 55 Inch 4K Smart TV",
        "Total: 64990.00"
    ]
    img_bytes = create_sample_receipt_image(lines)
    extracted_text, metadata = OCREngine.extract_text_from_image_bytes(img_bytes)
    
    assert len(extracted_text) > 0
    items, meta = ReceiptParser.parse_receipt(extracted_text)
    assert len(items) >= 1
