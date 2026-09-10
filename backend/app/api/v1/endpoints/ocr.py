from fastapi import APIRouter, Depends, UploadFile, File, status
from app.schemas.user import UserResponse
from app.schemas.ocr import (
    OCRScanResponse,
    OCRConfirmRequest,
    OCRConfirmResponse
)
from app.api.dependencies import get_current_user
from app.services.ocr_service import ocr_service

router = APIRouter()


@router.post(
    "/scan",
    response_model=OCRScanResponse,
    status_code=status.HTTP_200_OK,
    summary="Scan receipt image or PDF using OCR",
    description="Extracts raw text, normalizes content, and extracts candidate product details without saving to the database."
)
async def scan_receipt(
    file: UploadFile = File(..., description="Receipt image (JPEG/PNG/WEBP) or PDF invoice"),
    current_user: UserResponse = Depends(get_current_user)
) -> OCRScanResponse:
    """
    Executes OCR and heuristic receipt parsing.
    Returns extraction candidates and raw OCR text for user review and confirmation.
    """
    return await ocr_service.scan_receipt(file=file, user_id=current_user.id)


@router.post(
    "/confirm",
    response_model=OCRConfirmResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Confirm and persist OCR candidate items as products",
    description="Saves user-reviewed candidate items to MongoDB as products and optionally links the scanned receipt document."
)
async def confirm_receipt(
    payload: OCRConfirmRequest,
    current_user: UserResponse = Depends(get_current_user)
) -> OCRConfirmResponse:
    """
    Persists reviewed and edited receipt items as real user products.
    """
    return await ocr_service.confirm_and_save(user_id=current_user.id, payload=payload)
