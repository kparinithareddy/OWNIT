from typing import Optional, List
from fastapi import APIRouter, Depends, Query, status

from app.schemas.user import UserResponse
from app.schemas.warranty import (
    WarrantyCreate,
    WarrantyUpdate,
    WarrantyResponse,
    WarrantySummaryResponse
)
from app.api.dependencies import get_current_user
from app.services.warranty_service import warranty_service

router = APIRouter()


@router.post(
    "/",
    response_model=WarrantyResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Create a warranty component for a product",
    description="Registers a warranty component (e.g. Comprehensive, Panel, Compressor) for an owned product."
)
async def create_warranty(
    data: WarrantyCreate,
    current_user: UserResponse = Depends(get_current_user)
) -> WarrantyResponse:
    return await warranty_service.create_warranty(user_id=current_user.id, data=data)


@router.get(
    "/",
    response_model=List[WarrantyResponse],
    summary="List all warranties for current user",
    description="Retrieves all warranty components owned by the user with optional product and status filtering."
)
async def list_warranties(
    productId: Optional[str] = Query(None, description="Filter warranties by product ID"),
    status: Optional[str] = Query(None, description="Filter by status: 'Active', 'Expiring Soon', 'Expired'"),
    current_user: UserResponse = Depends(get_current_user)
) -> List[WarrantyResponse]:
    return await warranty_service.get_user_warranties(
        user_id=current_user.id,
        product_id=productId,
        status_filter=status
    )


@router.get(
    "/summary",
    response_model=WarrantySummaryResponse,
    summary="Get warranty status summary counts",
    description="Returns aggregate counts of Active, Expiring Soon, and Expired warranties for dashboard metrics."
)
async def get_warranty_summary(
    current_user: UserResponse = Depends(get_current_user)
) -> WarrantySummaryResponse:
    return await warranty_service.get_warranty_summary(user_id=current_user.id)


@router.get(
    "/product/{product_id}",
    response_model=List[WarrantyResponse],
    summary="List all warranty components for a specific product",
    description="Fetches all warranty components (e.g., Comprehensive + Panel) attached to a specific product."
)
async def get_product_warranties(
    product_id: str,
    current_user: UserResponse = Depends(get_current_user)
) -> List[WarrantyResponse]:
    return await warranty_service.get_product_warranties(
        product_id=product_id,
        user_id=current_user.id
    )


@router.get(
    "/{warranty_id}",
    response_model=WarrantyResponse,
    summary="Get warranty by ID",
    description="Retrieves a specific warranty component details."
)
async def get_warranty(
    warranty_id: str,
    current_user: UserResponse = Depends(get_current_user)
) -> WarrantyResponse:
    return await warranty_service.get_warranty_by_id(
        warranty_id=warranty_id,
        user_id=current_user.id
    )


@router.put(
    "/{warranty_id}",
    response_model=WarrantyResponse,
    summary="Update a warranty component",
    description="Updates warranty details, manually corrects dates, and recalculates expiry and status."
)
async def update_warranty(
    warranty_id: str,
    data: WarrantyUpdate,
    current_user: UserResponse = Depends(get_current_user)
) -> WarrantyResponse:
    return await warranty_service.update_warranty(
        warranty_id=warranty_id,
        user_id=current_user.id,
        data=data
    )


@router.delete(
    "/{warranty_id}",
    status_code=status.HTTP_200_OK,
    summary="Delete a warranty component",
    description="Permanently deletes a warranty component."
)
async def delete_warranty(
    warranty_id: str,
    current_user: UserResponse = Depends(get_current_user)
):
    await warranty_service.delete_warranty(
        warranty_id=warranty_id,
        user_id=current_user.id
    )
    return {
        "success": True,
        "message": "Warranty component successfully deleted.",
        "warrantyId": warranty_id
    }
