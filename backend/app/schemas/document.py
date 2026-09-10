from pydantic import BaseModel, Field
from datetime import datetime
from typing import Optional, List, Literal

DocumentTypeEnum = Literal[
    "Purchase Bill",
    "Warranty Card",
    "Extended Warranty",
    "User Manual",
    "Service Invoice",
    "Other"
]

VALID_DOCUMENT_TYPES = [
    "Purchase Bill",
    "Warranty Card",
    "Extended Warranty",
    "User Manual",
    "Service Invoice",
    "Other"
]


class DocumentResponse(BaseModel):
    id: str = Field(..., description="Unique document ID")
    userId: str = Field(..., description="Owner user ID")
    productId: str = Field(..., description="Associated product ID")
    documentType: str = Field(..., description="Type of document")
    originalFilename: str = Field(..., description="Original filename uploaded by the user")
    storedFilename: str = Field(..., description="Unique stored filename on server storage")
    mimeType: str = Field(..., description="MIME content type (e.g. application/pdf, image/jpeg)")
    fileSize: int = Field(..., description="File size in bytes")
    uploadedAt: datetime = Field(..., description="Upload timestamp (UTC)")
    productName: Optional[str] = Field(default=None, description="Linked product name for convenient UI display")
    productBrand: Optional[str] = Field(default=None, description="Linked product brand")

    model_config = {
        "from_attributes": True,
        "json_schema_extra": {
            "example": {
                "id": "673abc4567890efabcdef123",
                "userId": "66dbb01234abcd5678ef9012",
                "productId": "673abc1234567890efabcdef",
                "documentType": "Purchase Bill",
                "originalFilename": "Amazon_Invoice_MacBook.pdf",
                "storedFilename": "66dbb012_673abc12_f891a20c.pdf",
                "mimeType": "application/pdf",
                "fileSize": 1420500,
                "uploadedAt": "2026-09-10T11:30:00Z",
                "productName": "MacBook Pro 14",
                "productBrand": "Apple"
            }
        }
    }


class DocumentListResponse(BaseModel):
    items: List[DocumentResponse]
    total: int
