from typing import Optional, List
from fastapi import APIRouter, Depends, Query, status

from app.schemas.user import UserResponse
from app.schemas.product import (
    ProductCreate,
    ProductUpdate,
    ProductResponse,
    ProductListResponse
)
from app.schemas.timeline import (
    TimelineEvent,
    TimelineEventCreate,
    TimelineResponse
)
from app.schemas.life_score import LifeScoreResponse
from app.api.dependencies import get_current_user
from app.services.product_service import product_service
from app.services.timeline_service import timeline_service
from app.services.life_score_service import life_score_service


router = APIRouter()


@router.post(
    "/",
    response_model=ProductResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Create a new product",
    description="Adds a new physical asset/product belonging to the authenticated user."
)
async def create_product(
    data: ProductCreate,
    current_user: UserResponse = Depends(get_current_user)
) -> ProductResponse:
    """
    Creates a product scoped to the current authenticated user's ID.
    """
    return await product_service.create_product(current_user.id, data)


@router.get(
    "/brands",
    response_model=List[str],
    summary="Get user product brands",
    description="Returns distinct product brands recorded in the user's vault."
)
async def list_user_brands(
    current_user: UserResponse = Depends(get_current_user)
) -> List[str]:
    """
    Returns unique brands registered by the authenticated user for dynamic filtering.
    """
    return await product_service.get_user_brands(user_id=current_user.id)


@router.get(
    "/",
    response_model=List[ProductResponse],
    summary="List and filter all products for the current user",
    description="Returns all products owned by the authenticated user with multi-field search and backend filtering."
)
async def list_products(
    search: Optional[str] = Query(None, description="Search term across name, brand, model, and serial number"),
    category: Optional[str] = Query(None, description="Filter by category (e.g. Mobile, Laptop, TV)"),
    brand: Optional[str] = Query(None, description="Filter by brand"),
    warrantyStatus: Optional[str] = Query(None, description="Filter by warranty status: active, expiring_soon, expired, all"),
    returnStatus: Optional[str] = Query(None, description="Filter by return window: active, expired, all"),
    maintenanceStatus: Optional[str] = Query(None, description="Filter by maintenance: due, overdue, up_to_date, all"),
    sortBy: Optional[str] = Query("createdAt", description="Field to sort by: createdAt, name, price, purchaseDate, brand"),
    sortOrder: Optional[str] = Query("desc", description="Sort direction: asc, desc"),
    current_user: UserResponse = Depends(get_current_user)
) -> List[ProductResponse]:
    """
    Lists products strictly scoped to current_user.id with full server-side filtering and sorting.
    """
    return await product_service.get_user_products(
        user_id=current_user.id,
        category=category,
        brand=brand,
        search=search,
        warranty_status=warrantyStatus,
        return_status=returnStatus,
        maintenance_status=maintenanceStatus,
        sort_by=sortBy,
        sort_order=sortOrder
    )


@router.get(
    "/{product_id}",
    response_model=ProductResponse,
    summary="Get product by ID",
    description="Fetches product details by ID. Only the product owner can access this record."
)
async def get_product(
    product_id: str,
    current_user: UserResponse = Depends(get_current_user)
) -> ProductResponse:
    """
    Retrieves a single product, ensuring current_user is the owner.
    """
    return await product_service.get_product_by_id(product_id, current_user.id)


@router.put(
    "/{product_id}",
    response_model=ProductResponse,
    summary="Update an existing product",
    description="Updates product fields. Only the product owner can modify this record."
)
async def update_product(
    product_id: str,
    data: ProductUpdate,
    current_user: UserResponse = Depends(get_current_user)
) -> ProductResponse:
    """
    Updates a product, ensuring current_user is the owner.
    """
    return await product_service.update_product(product_id, current_user.id, data)


@router.delete(
    "/{product_id}",
    status_code=status.HTTP_200_OK,
    summary="Delete a product",
    description="Permanently deletes a product record. Only the product owner can delete their item."
)
async def delete_product(
    product_id: str,
    current_user: UserResponse = Depends(get_current_user)
):
    """
    Deletes a product, ensuring current_user is the owner.
    """
    await product_service.delete_product(product_id, current_user.id)
    return {
        "success": True,
        "message": "Product successfully deleted.",
        "productId": product_id
    }


@router.get(
    "/{product_id}/timeline",
    response_model=TimelineResponse,
    summary="Get product lifecycle timeline",
    description="Retrieves the full chronological lifecycle timeline computed from purchase, return windows, warranty milestones, documents, and service logs."
)
async def get_product_timeline(
    product_id: str,
    current_user: UserResponse = Depends(get_current_user)
) -> TimelineResponse:
    return await timeline_service.get_product_timeline(product_id, current_user.id)


@router.post(
    "/{product_id}/timeline",
    response_model=TimelineEvent,
    status_code=status.HTTP_201_CREATED,
    summary="Log custom lifecycle event",
    description="Adds a service, maintenance, repair, or custom milestone to the product lifecycle timeline."
)
async def add_lifecycle_event(
    product_id: str,
    data: TimelineEventCreate,
    current_user: UserResponse = Depends(get_current_user)
) -> TimelineEvent:
    return await timeline_service.add_custom_lifecycle_event(product_id, current_user.id, data)


@router.get(
    "/{product_id}/life-score",
    response_model=LifeScoreResponse,
    summary="Get Product Life Score",
    description="Computes a transparent, rule-based Product Life Score (0-100) with explainable reasons and improvement tips."
)
async def get_product_life_score(
    product_id: str,
    current_user: UserResponse = Depends(get_current_user)
) -> LifeScoreResponse:
    """
    Computes transparent life score based on warranty coverage, documents, maintenance, device age, and deadlines.
    """
    return await life_score_service.calculate_life_score(product_id, current_user.id)


