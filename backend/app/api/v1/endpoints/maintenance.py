from typing import List
from fastapi import APIRouter, Depends, status

from app.api.dependencies import get_current_user
from app.schemas.user import UserResponse
from app.schemas.maintenance import (
    MaintenanceCreate,
    MaintenanceUpdate,
    MaintenanceResponse,
    MaintenanceRecommendation
)
from app.services.maintenance_service import maintenance_service

router = APIRouter()


@router.post(
    "/",
    response_model=MaintenanceResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Create maintenance log record",
    description="Logs a new routine servicing, inspection, or maintenance event for a product."
)
async def create_maintenance(
    data: MaintenanceCreate,
    current_user: UserResponse = Depends(get_current_user)
) -> MaintenanceResponse:
    return await maintenance_service.create_record(current_user.id, data)


@router.get(
    "/product/{product_id}",
    response_model=List[MaintenanceResponse],
    summary="List maintenance history for product",
    description="Retrieves all maintenance and service records for a specific product."
)
async def list_product_maintenance(
    product_id: str,
    current_user: UserResponse = Depends(get_current_user)
) -> List[MaintenanceResponse]:
    return await maintenance_service.get_records_by_product(product_id, current_user.id)


@router.get(
    "/product/{product_id}/recommendations",
    response_model=List[MaintenanceRecommendation],
    summary="Get maintenance recommendations for product",
    description="Retrieves structured preventive care guidelines with explicit sourcing and transparency disclaimers."
)
async def get_maintenance_recommendations(
    product_id: str,
    current_user: UserResponse = Depends(get_current_user)
) -> List[MaintenanceRecommendation]:
    return await maintenance_service.get_recommendations_for_product(product_id, current_user.id)


@router.get(
    "/{maintenance_id}",
    response_model=MaintenanceResponse,
    summary="Get maintenance record by ID",
    description="Retrieves a single maintenance record ensuring user ownership."
)
async def get_maintenance(
    maintenance_id: str,
    current_user: UserResponse = Depends(get_current_user)
) -> MaintenanceResponse:
    return await maintenance_service.get_record_by_id(maintenance_id, current_user.id)


@router.put(
    "/{maintenance_id}",
    response_model=MaintenanceResponse,
    summary="Update maintenance record",
    description="Updates an existing maintenance record."
)
async def update_maintenance(
    maintenance_id: str,
    data: MaintenanceUpdate,
    current_user: UserResponse = Depends(get_current_user)
) -> MaintenanceResponse:
    return await maintenance_service.update_record(maintenance_id, current_user.id, data)


@router.delete(
    "/{maintenance_id}",
    status_code=status.HTTP_200_OK,
    summary="Delete maintenance record",
    description="Permanently deletes a maintenance record."
)
async def delete_maintenance(
    maintenance_id: str,
    current_user: UserResponse = Depends(get_current_user)
):
    await maintenance_service.delete_record(maintenance_id, current_user.id)
    return {"success": True, "message": "Maintenance record successfully deleted."}
