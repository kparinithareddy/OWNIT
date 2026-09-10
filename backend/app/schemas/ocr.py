from pydantic import BaseModel, Field
from typing import Optional, List, Any, Dict
from datetime import date, datetime
from app.schemas.product import ProductResponse
from app.schemas.document import DocumentResponse


class OCRExtractedItem(BaseModel):
    name: str = Field(..., description="Detected product or item name")
    brand: Optional[str] = Field(None, description="Detected brand / manufacturer")
    model: Optional[str] = Field(None, description="Detected model name or number")
    category: str = Field("Other", description="Assigned product category")
    purchaseDate: Optional[str] = Field(None, description="Detected purchase date")
    price: Optional[float] = Field(None, ge=0.0, description="Extracted price")
    quantity: int = Field(1, ge=1, description="Extracted quantity")
    seller: Optional[str] = Field(None, description="Detected merchant / store name")
    serialNumber: Optional[str] = Field(None, description="Detected serial number")
    imei: Optional[str] = Field(None, description="Detected IMEI number")
    warrantyInfo: Optional[str] = Field(None, description="Extracted warranty or guarantee notes")
    confidence: float = Field(0.8, ge=0.0, le=1.0, description="Confidence score")
    confidenceLevel: str = Field("medium", description="'high', 'medium', or 'low'")
    uncertainFields: List[str] = Field(default_factory=list, description="Fields where confidence is low")


class OCRScanResponse(BaseModel):
    seller: Optional[str] = Field(None, description="Overall detected store / merchant name")
    invoiceNumber: Optional[str] = Field(None, description="Detected invoice or receipt number")
    invoiceDate: Optional[str] = Field(None, description="Detected invoice date")
    totalAmount: Optional[float] = Field(None, description="Detected grand total amount")
    currency: str = Field("INR", description="Detected or default currency symbol/code")
    overallConfidence: float = Field(0.8, ge=0.0, le=1.0, description="Aggregate confidence score")
    overallConfidenceLevel: str = Field("medium", description="'high', 'medium', or 'low'")
    items: List[OCRExtractedItem] = Field(default_factory=list, description="List of candidate items found on receipt")
    rawText: str = Field(..., description="Raw extracted OCR text preserved for debugging and audit")
    pageCount: int = Field(1, description="Number of pages processed")
    processingTimeMs: int = Field(0, description="Time taken to extract and parse in milliseconds")
    warnings: List[str] = Field(default_factory=list, description="Helpful non-blocking warnings or guidance")
    tempFileToken: Optional[str] = Field(None, description="Temporary token referencing uploaded file")
    originalFilename: Optional[str] = None
    fileSize: int = 0
    mimeType: str = ""


class OCRConfirmItem(BaseModel):
    name: str = Field(..., min_length=1, max_length=200)
    brand: Optional[str] = Field(None, max_length=100)
    model: Optional[str] = Field(None, max_length=100)
    category: str = Field("Other")
    purchaseDate: Optional[str] = None
    price: Optional[float] = Field(None, ge=0.0)
    quantity: int = Field(1, ge=1)
    seller: Optional[str] = Field(None, max_length=200)
    serialNumber: Optional[str] = Field(None, max_length=100)
    imei: Optional[str] = Field(None, max_length=50)
    notes: Optional[str] = None


class OCRConfirmRequest(BaseModel):
    items: List[OCRConfirmItem] = Field(..., min_length=1, description="List of confirmed products to save")
    tempFileToken: Optional[str] = Field(None, description="Optional temp token to link receipt file")
    documentType: str = Field("Purchase Bill", description="Document type for attached receipt file")


class OCRConfirmResponse(BaseModel):
    createdProducts: List[ProductResponse] = Field(default_factory=list)
    attachedDocuments: List[DocumentResponse] = Field(default_factory=list)
    message: str = "Products successfully created from receipt."
