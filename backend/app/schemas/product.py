from pydantic import BaseModel, Field, field_validator
from datetime import datetime
from typing import Optional, List, Literal

ProductCategoryType = Literal[
    "Mobile",
    "Laptop",
    "TV",
    "Refrigerator",
    "Washing Machine",
    "Air Conditioner",
    "Audio",
    "Camera",
    "Gaming",
    "Home Appliance",
    "Other"
]

VALID_CATEGORIES = [
    "Mobile",
    "Laptop",
    "TV",
    "Refrigerator",
    "Washing Machine",
    "Air Conditioner",
    "Audio",
    "Camera",
    "Gaming",
    "Home Appliance",
    "Other"
]


class ProductCreate(BaseModel):
    name: str = Field(..., min_length=1, max_length=120, description="Product name (e.g. MacBook Pro 14)")
    brand: str = Field(..., min_length=1, max_length=100, description="Brand / Manufacturer (e.g. Apple)")
    model: str = Field(..., min_length=1, max_length=100, description="Model name or number")
    category: ProductCategoryType = Field(default="Other", description="Product category")
    purchaseDate: str = Field(..., description="Date of purchase (YYYY-MM-DD)")
    price: float = Field(..., ge=0, description="Base purchase price before taxes / subtotal")
    taxAmount: Optional[float] = Field(default=None, ge=0, description="GST / Tax amount")
    totalPrice: Optional[float] = Field(default=None, ge=0, description="Total price inclusive of GST / tax")
    quantity: int = Field(default=1, ge=1, description="Quantity purchased")
    seller: Optional[str] = Field(default=None, max_length=120, description="Store or vendor name")
    sellerAddress: Optional[str] = Field(default=None, max_length=300, description="Store or vendor address")
    paymentMethod: Optional[str] = Field(default=None, max_length=100, description="Payment method used (e.g. UPI, Credit Card, Cash)")
    serialNumber: Optional[str] = Field(default=None, max_length=100, description="Unique serial number")
    imei: Optional[str] = Field(default=None, max_length=50, description="IMEI number (for mobile/cellular devices)")
    image: Optional[str] = Field(default=None, description="Image URL or placeholder identifier")
    notes: Optional[str] = Field(default=None, max_length=1000, description="Additional notes or specifications")
    # Return & Replacement tracking fields
    returnDuration: Optional[str] = Field(default=None, description="Return duration (e.g. '7 Days', '10 Days', '14 Days', '30 Days')")
    returnStartDate: Optional[str] = Field(default=None, description="Return period start date (YYYY-MM-DD)")
    returnDeadline: Optional[str] = Field(default=None, description="Return deadline date (YYYY-MM-DD)")
    returnPolicySource: Optional[str] = Field(default=None, description="Source of policy information (e.g. 'Amazon India Replacement Policy', 'Store Receipt')")

    @field_validator("name", "brand", "model")
    @classmethod
    def strip_whitespace(cls, v: str) -> str:
        clean = v.strip()
        if not clean:
            raise ValueError("Field cannot be blank or empty whitespace")
        return clean


class ProductUpdate(BaseModel):
    name: Optional[str] = Field(default=None, min_length=1, max_length=120)
    brand: Optional[str] = Field(default=None, min_length=1, max_length=100)
    model: Optional[str] = Field(default=None, min_length=1, max_length=100)
    category: Optional[ProductCategoryType] = None
    purchaseDate: Optional[str] = None
    price: Optional[float] = Field(default=None, ge=0)
    taxAmount: Optional[float] = Field(default=None, ge=0)
    totalPrice: Optional[float] = Field(default=None, ge=0)
    quantity: Optional[int] = Field(default=None, ge=1)
    seller: Optional[str] = Field(default=None, max_length=120)
    sellerAddress: Optional[str] = Field(default=None, max_length=300)
    paymentMethod: Optional[str] = Field(default=None, max_length=100)
    serialNumber: Optional[str] = Field(default=None, max_length=100)
    imei: Optional[str] = Field(default=None, max_length=50)
    image: Optional[str] = None
    notes: Optional[str] = Field(default=None, max_length=1000)
    # Return & Replacement tracking fields
    returnDuration: Optional[str] = None
    returnStartDate: Optional[str] = None
    returnDeadline: Optional[str] = None
    returnPolicySource: Optional[str] = None

    @field_validator("name", "brand", "model")
    @classmethod
    def strip_optional_whitespace(cls, v: Optional[str]) -> Optional[str]:
        if v is not None:
            clean = v.strip()
            if not clean:
                raise ValueError("Field cannot be blank")
            return clean
        return v


class ProductResponse(BaseModel):
    id: str = Field(..., description="Unique product identifier")
    userId: str = Field(..., description="Owner user ID")
    name: str
    brand: str
    model: str
    category: str
    purchaseDate: str
    price: float
    taxAmount: Optional[float] = None
    totalPrice: Optional[float] = None
    quantity: int = 1
    seller: Optional[str] = None
    sellerAddress: Optional[str] = None
    paymentMethod: Optional[str] = None
    serialNumber: Optional[str] = None
    imei: Optional[str] = None
    image: Optional[str] = None
    notes: Optional[str] = None
    # Return tracking properties
    returnDuration: Optional[str] = None
    returnStartDate: Optional[str] = None
    returnDeadline: Optional[str] = None
    returnPolicySource: Optional[str] = None
    returnStatus: str = "Unknown"
    returnDaysRemaining: Optional[int] = None
    createdAt: datetime
    updatedAt: datetime

    model_config = {
        "from_attributes": True,
        "json_schema_extra": {
            "example": {
                "id": "673abc1234567890efabcdef",
                "userId": "66dbb01234abcd5678ef9012",
                "name": "Sony WH-1000XM5",
                "brand": "Sony",
                "model": "WH-1000XM5 Silver",
                "category": "Audio",
                "purchaseDate": "2024-03-15",
                "price": 26990.0,
                "quantity": 1,
                "seller": "Amazon India",
                "serialNumber": "S01-9482910-B",
                "imei": None,
                "image": None,
                "notes": "Purchased during Great Republic Day Sale",
                "returnDuration": "7 Days",
                "returnStartDate": "2024-03-15",
                "returnDeadline": "2024-03-22",
                "returnPolicySource": "Amazon India Standard Replacement Policy",
                "returnStatus": "Expired",
                "returnDaysRemaining": -890,
                "createdAt": "2026-09-10T11:00:00Z",
                "updatedAt": "2026-09-10T11:00:00Z"
            }
        }
    }


class ProductListResponse(BaseModel):
    items: List[ProductResponse]
    total: int
