from typing import List
from fastapi import APIRouter, Depends, status

from app.schemas.user import UserResponse
from app.schemas.service_history import (
    ServiceRecordCreate,
    ServiceRecordUpdate,
    ServiceRecordResponse
)
from app.api.dependencies import get_current_user
from app.services.service_history_service import service_history_service

router = APIRouter()


@router.post(
    "/",
    response_model=ServiceRecordResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Create a service/repair record",
    description="Logs a physical service, repair, or inspection event for an asset with service date, problem, center, work performed, cost, and warranty coverage status."
)
async def create_service_record(
    data: ServiceRecordCreate,
    current_user: UserResponse = Depends(get_current_user)
) -> ServiceRecordResponse:
    """
    Creates a new service history log ensuring owner isolation.
    """
    return await service_history_service.create_service_record(
        user_id=current_user.id,
        data=data
    )


@router.get(
    "/product/{product_id}",
    response_model=List[ServiceRecordResponse],
    summary="List all service records for a product",
    description="Retrieves chronological service and repair history for the specified product owned by current user."
)
async def list_service_records_by_product(
    product_id: str,
    current_user: UserResponse = Depends(get_current_user)
) -> List[ServiceRecordResponse]:
    """
    Lists product service records with strict user isolation.
    """
    return await service_history_service.get_service_records_by_product(
        product_id=product_id,
        user_id=current_user.id
    )


@router.get(
    "/{id}",
    response_model=ServiceRecordResponse,
    summary="Get single service record",
    description="Retrieves a specific service history record verifying owner isolation."
)
async def get_service_record(
    id: str,
    current_user: UserResponse = Depends(get_current_user)
) -> ServiceRecordResponse:
    return await service_history_service.get_service_record_by_id(
        service_id=id,
        user_id=current_user.id
    )


@router.put(
    "/{id}",
    response_model=ServiceRecordResponse,
    summary="Update service record",
    description="Modifies details of an existing service record."
)
async def update_service_record(
    id: str,
    data: ServiceRecordUpdate,
    current_user: UserResponse = Depends(get_current_user)
) -> ServiceRecordResponse:
    return await service_history_service.update_service_record(
        service_id=id,
        user_id=current_user.id,
        data=data
    )


@router.delete(
    "/{id}",
    status_code=status.HTTP_200_OK,
    summary="Delete service record",
    description="Deletes a service history record."
)
async def delete_service_record(
    id: str,
    current_user: UserResponse = Depends(get_current_user)
):
    await service_history_service.delete_service_record(
        service_id=id,
        user_id=current_user.id
    )
    return {
        "success": True,
        "message": f"Service record '{id}' was successfully deleted."
    }
