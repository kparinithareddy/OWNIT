from fastapi import APIRouter, Depends, status
from app.schemas.user import UserResponse
from app.schemas.claim_assistant import (
    ClaimPreparationRequest,
    ClaimPreparationResponse
)
from app.api.dependencies import get_current_user
from app.services.claim_assistant_service import claim_assistant_service

router = APIRouter()


@router.post(
    "/prepare",
    response_model=ClaimPreparationResponse,
    status_code=status.HTTP_200_OK,
    summary="Prepare a comprehensive warranty claim dossier",
    description="Generates a structured, provenance-tagged warranty claim preparation dossier, editable draft support message, and review checklist. Does NOT submit claims or contact manufacturers automatically."
)
async def prepare_warranty_claim(
    data: ClaimPreparationRequest,
    current_user: UserResponse = Depends(get_current_user)
) -> ClaimPreparationResponse:
    """
    Synthesizes product data, warranty status, documented coverage, relevant exclusions,
    required documents, official contact information, and an editable draft message.
    """
    return await claim_assistant_service.prepare_claim_dossier(
        user_id=current_user.id,
        request=data
    )
