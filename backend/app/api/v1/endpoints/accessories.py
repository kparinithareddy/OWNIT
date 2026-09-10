from fastapi import APIRouter, Depends, Query, status
from typing import Optional, List
from app.schemas.user import UserResponse
from app.schemas.accessory import AccessoryRecommendationsResponse
from app.services.accessory_service import accessory_service
from app.api.dependencies import get_current_user

router = APIRouter()


@router.get(
    "/recommendations",
    response_model=AccessoryRecommendationsResponse,
    status_code=status.HTTP_200_OK,
    summary="Get Compatible Accessory Recommendations",
    description="Returns verified compatible and potentially compatible accessories grounded in product brand, model, specs, and budget."
)
async def get_accessory_recommendations(
    productId: str = Query(..., description="Target product identifier"),
    category: Optional[str] = Query(None, description="Optional accessory category filter (e.g. soundbar, wall mount, HDMI cable, surge protector)"),
    minBudget: Optional[float] = Query(None, ge=0, description="Minimum price filter in INR"),
    maxBudget: Optional[float] = Query(None, ge=0, description="Maximum price filter in INR"),
    current_user: UserResponse = Depends(get_current_user)
) -> AccessoryRecommendationsResponse:
    """
    Returns curated, verified compatible accessories for the selected asset with budget filtering.
    """
    return await accessory_service.get_product_recommendations(
        user_id=current_user.id,
        product_id=productId,
        category=category,
        min_budget=minBudget,
        max_budget=maxBudget
    )


@router.get(
    "/categories",
    response_model=List[str],
    status_code=status.HTTP_200_OK,
    summary="Get Available Accessory Categories",
    description="Returns available accessory categories relevant to the specified product."
)
async def get_accessory_categories(
    productId: str = Query(..., description="Target product identifier"),
    current_user: UserResponse = Depends(get_current_user)
) -> List[str]:
    """
    Returns unique categories of compatible accessories available for the product.
    """
    return await accessory_service.get_available_categories(
        user_id=current_user.id,
        product_id=productId
    )
