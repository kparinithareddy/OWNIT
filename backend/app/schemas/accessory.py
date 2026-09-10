from pydantic import BaseModel, Field
from typing import List, Optional, Literal, Dict, Any


class AccessoryRecommendation(BaseModel):
    id: str = Field(..., description="Unique identifier for the accessory recommendation")
    name: str = Field(..., description="Name / title of the accessory")
    category: str = Field(..., description="Accessory category (e.g. soundbar, wall mount, hdmi cable, surge protector)")
    brand: str = Field(..., description="Accessory manufacturer or brand")
    model: Optional[str] = Field(None, description="Accessory model number where applicable")
    price: float = Field(..., description="Price in INR (₹)")
    priceFormatted: str = Field(..., description="Formatted price string (e.g. ₹7,499)")
    compatibilityStatus: Literal["Compatible", "Potentially compatible"] = Field(
        ...,
        description="Strict compatibility tier: 'Compatible' or 'Potentially compatible'"
    )
    compatibilityReason: str = Field(
        ...,
        description="Factual evidence or technical justification for compatibility with the host product"
    )
    platform: str = Field(..., description="Platform / store / vendor source (e.g. Samsung Official Store, Croma, Belkin)")
    sourceUrl: Optional[str] = Field(None, description="Direct URL to open original source product page")
    rating: Optional[float] = Field(None, ge=1.0, le=5.0, description="Customer rating out of 5.0")
    reviewCount: Optional[int] = Field(None, ge=0, description="Total verified review count")
    imageUrl: Optional[str] = Field(None, description="Product image / icon thumbnail")
    inBudget: bool = Field(default=True, description="Whether the price falls within the user's requested budget range")


class AccessoryQueryRequest(BaseModel):
    productId: str = Field(..., description="ID of the target registered product")
    category: Optional[str] = Field(None, description="Filter by accessory category (e.g. soundbar, wall mount, hdmi cable, surge protector)")
    minBudget: Optional[float] = Field(None, ge=0, description="Minimum budget in INR")
    maxBudget: Optional[float] = Field(None, ge=0, description="Maximum budget in INR")


class AccessoryRecommendationsResponse(BaseModel):
    productId: str = Field(..., description="Target product ID")
    productName: str = Field(..., description="Target product name")
    brand: str = Field(..., description="Target product brand")
    model: str = Field(..., description="Target product model")
    category: str = Field(..., description="Target product category")
    appliedBudget: Optional[Dict[str, Optional[float]]] = Field(
        default=None,
        description="Applied min/max budget filter range"
    )
    appliedCategory: Optional[str] = Field(
        default=None,
        description="Applied accessory category filter"
    )
    recommendations: List[AccessoryRecommendation] = Field(
        default_factory=list,
        description="List of ranked compatible and potentially compatible accessories"
    )
    totalCount: int = Field(..., description="Total count of matching accessories")
