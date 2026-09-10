from fastapi import APIRouter, Depends, Path, status
from app.schemas.user import UserResponse
from app.schemas.safety_recall import (
    ProductRecallCheckResponse,
    VaultRecallSummaryResponse
)
from app.services.recall_service import recall_service
from app.api.dependencies import get_current_user

router = APIRouter()


@router.get(
    "/check/{productId}",
    response_model=ProductRecallCheckResponse,
    status_code=status.HTTP_200_OK,
    summary="Check Safety Recall Status for Product",
    description="Cross-references product brand, model, and serial number against verified manufacturer safety bulletins."
)
async def check_product_recall(
    productId: str = Path(..., description="Target product unique identifier"),
    current_user: UserResponse = Depends(get_current_user)
) -> ProductRecallCheckResponse:
    """
    Evaluates safety bulletins and recall notices for the specified user-owned asset.
    """
    return await recall_service.check_product(
        user_id=current_user.id,
        product_id=productId
    )


@router.get(
    "/vault-scan",
    response_model=VaultRecallSummaryResponse,
    status_code=status.HTTP_200_OK,
    summary="Scan Entire Vault for Safety Recalls",
    description="Scans all registered assets in the authenticated user's vault and returns active recall warnings."
)
async def scan_vault_recalls(
    current_user: UserResponse = Depends(get_current_user)
) -> VaultRecallSummaryResponse:
    """
    Scans the user's entire product vault against official safety registries and regulatory bulletins.
    """
    return await recall_service.scan_user_vault(user_id=current_user.id)
