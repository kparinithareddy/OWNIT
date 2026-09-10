from pydantic import BaseModel, Field
from typing import Optional, List, Dict, Any
from datetime import datetime, date


WARRANTY_TYPES = [
    "Comprehensive Warranty",
    "Manufacturer Warranty",
    "Panel Warranty",
    "Compressor Warranty",
    "Motor Warranty",
    "Extended Warranty",
    "Screen Protection",
    "Accidental Damage Protection",
    "Battery Warranty",
    "Other"
]


class WarrantyCreate(BaseModel):
    """
    Schema for registering a new warranty component for a product.
    """
    productId: str = Field(..., description="ID of the product this warranty covers")
    type: str = Field("Comprehensive Warranty", description="Type of warranty component")
    provider: Optional[str] = Field(None, max_length=150, description="Warranty provider / brand / insurer")
    duration: Optional[str] = Field(None, max_length=50, description="Duration description, e.g., '2 Years', '24 Months'")
    startDate: str = Field(..., description="Start date of coverage in YYYY-MM-DD")
    expiryDate: Optional[str] = Field(None, description="Expiry date in YYYY-MM-DD. Auto-calculated from duration if omitted.")
    benefits: Optional[str] = Field(None, description="Covered benefits and repair services")
    exclusions: Optional[str] = Field(None, description="Explicit exclusions like liquid/physical damage")
    conditions: Optional[str] = Field(None, description="Conditions for claim validity")
    claimProcedure: Optional[str] = Field(None, description="Step-by-step claim instructions")
    requiredDocuments: List[str] = Field(default_factory=list, description="Documents required during claim submission")
    serviceInformation: Optional[str] = Field(None, description="Customer care numbers, email, or service center info")


class WarrantyUpdate(BaseModel):
    """
    Schema for updating an existing warranty component.
    """
    type: Optional[str] = None
    provider: Optional[str] = None
    duration: Optional[str] = None
    startDate: Optional[str] = None
    expiryDate: Optional[str] = None
    benefits: Optional[str] = None
    exclusions: Optional[str] = None
    conditions: Optional[str] = None
    claimProcedure: Optional[str] = None
    requiredDocuments: Optional[List[str]] = None
    serviceInformation: Optional[str] = None


class WarrantyResponse(BaseModel):
    """
    Full typed warranty response schema including backend-calculated status.
    """
    id: str
    productId: str
    userId: str
    productName: Optional[str] = None
    productBrand: Optional[str] = None
    productCategory: Optional[str] = None
    type: str
    provider: Optional[str] = None
    duration: Optional[str] = None
    startDate: str
    expiryDate: str
    status: str = Field(..., description="'Active', 'Expiring Soon', or 'Expired'")
    daysRemaining: int = Field(..., description="Days until expiry (positive) or days since expired (negative)")
    statusColor: str = Field(..., description="'green', 'amber', or 'red'")
    benefits: Optional[str] = None
    exclusions: Optional[str] = None
    conditions: Optional[str] = None
    claimProcedure: Optional[str] = None
    requiredDocuments: List[str] = Field(default_factory=list)
    serviceInformation: Optional[str] = None
    createdAt: datetime
    updatedAt: datetime


class WarrantySummaryResponse(BaseModel):
    """
    Summary counts and expiring items for dashboard widgets.
    """
    totalWarranties: int = 0
    activeCount: int = 0
    expiringSoonCount: int = 0
    expiredCount: int = 0
    expiringSoonItems: List[WarrantyResponse] = Field(default_factory=list)
