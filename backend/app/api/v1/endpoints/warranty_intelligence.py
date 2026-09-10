from fastapi import APIRouter, Depends, Query, status
from app.schemas.user import UserResponse
from app.schemas.warranty_intelligence import (
    WarrantyQuestionRequest,
    WarrantyQuestionType,
    WarrantyIntelligenceResponse
)
from app.api.dependencies import get_current_user
from app.services.warranty_intelligence_service import warranty_intelligence_service

router = APIRouter()


@router.post(
    "/analyze",
    response_model=WarrantyIntelligenceResponse,
    status_code=status.HTTP_200_OK,
    summary="Analyze warranty coverage & intelligence",
    description="Executes the structured 9-step Warranty Intelligence pipeline on a user problem or standard warranty query, returning coverage likelihood (confirmed, likely, unclear, excluded), conditions, verified sources, and recommended claim steps."
)
async def analyze_warranty_intelligence(
    data: WarrantyQuestionRequest,
    current_user: UserResponse = Depends(get_current_user)
) -> WarrantyIntelligenceResponse:
    """
    Evaluates issue coverage, active status, inclusions, exclusions, claim procedures,
    or document readiness with strict probabilistic phrasing and non-guarantee guardrails.
    """
    return await warranty_intelligence_service.analyze_issue_or_question(
        user_id=current_user.id,
        request=data
    )


@router.get(
    "/quick-check/{product_id}",
    response_model=WarrantyIntelligenceResponse,
    status_code=status.HTTP_200_OK,
    summary="Quick warranty query check",
    description="Quickly evaluates one of the 5 standard warranty questions (is_active, what_covered, what_excluded, how_to_claim, required_documents)."
)
async def quick_check_warranty(
    product_id: str,
    question_type: WarrantyQuestionType = Query(WarrantyQuestionType.IS_ACTIVE, alias="questionType"),
    current_user: UserResponse = Depends(get_current_user)
) -> WarrantyIntelligenceResponse:
    """
    Executes a fast pre-packaged intelligence query for the product.
    """
    req = WarrantyQuestionRequest(
        productId=product_id,
        questionType=question_type
    )
    return await warranty_intelligence_service.analyze_issue_or_question(
        user_id=current_user.id,
        request=req
    )
