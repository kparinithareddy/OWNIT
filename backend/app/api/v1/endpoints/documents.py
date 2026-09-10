from typing import Optional, List
from fastapi import APIRouter, Depends, Query, UploadFile, File, Form, status
from fastapi.responses import FileResponse

from app.schemas.user import UserResponse
from app.schemas.document import DocumentResponse, DocumentListResponse
from app.api.dependencies import get_current_user
from app.services.document_service import document_service

router = APIRouter()


@router.post(
    "/upload",
    response_model=DocumentResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Upload a document or receipt for a product",
    description="Uploads and stores a PDF or image document (bill, warranty card, manual) linked to a user's product."
)
async def upload_document(
    productId: str = Form(..., description="ID of the product this document belongs to"),
    documentType: str = Form(..., description="Type: Purchase Bill, Warranty Card, Extended Warranty, User Manual, Service Invoice, Other"),
    file: UploadFile = File(..., description="Document file (PDF, JPG, PNG, WEBP) max 10MB"),
    current_user: UserResponse = Depends(get_current_user)
) -> DocumentResponse:
    """
    Handles file upload, validates format & size, stores file to disk, and indexes in MongoDB.
    """
    return await document_service.upload_document(
        user_id=current_user.id,
        product_id=productId,
        document_type=documentType,
        file=file
    )


@router.get(
    "/",
    response_model=List[DocumentResponse],
    summary="List all documents for current user",
    description="Returns all documents owned by the authenticated user with optional filtering by product or document type."
)
async def list_documents(
    productId: Optional[str] = Query(None, description="Filter by product ID"),
    documentType: Optional[str] = Query(None, description="Filter by document type"),
    current_user: UserResponse = Depends(get_current_user)
) -> List[DocumentResponse]:
    """
    Lists documents strictly scoped to current_user.id.
    """
    return await document_service.list_user_documents(
        user_id=current_user.id,
        product_id=productId,
        document_type=documentType
    )


@router.get(
    "/{document_id}",
    response_model=DocumentResponse,
    summary="Get document metadata by ID",
    description="Fetches document details. Only the document owner can access this metadata."
)
async def get_document(
    document_id: str,
    current_user: UserResponse = Depends(get_current_user)
) -> DocumentResponse:
    """
    Retrieves document metadata, ensuring current_user is the owner.
    """
    return await document_service.get_document_response(document_id, current_user.id)


@router.get(
    "/{document_id}/download",
    summary="Download or view document file",
    description="Streams the raw document file (PDF / Image) for viewing or downloading. Only the document owner can access it."
)
async def download_document(
    document_id: str,
    download: bool = Query(False, description="Set true to force browser download attachment, false to view inline"),
    current_user: UserResponse = Depends(get_current_user)
):
    """
    Returns a FileResponse with appropriate MIME type and Content-Disposition.
    """
    file_path, original_filename, mime_type = await document_service.get_file_for_download(
        document_id=document_id,
        user_id=current_user.id
    )

    disposition_type = "attachment" if download else "inline"
    headers = {
        "Content-Disposition": f'{disposition_type}; filename="{original_filename}"'
    }

    return FileResponse(
        path=file_path,
        media_type=mime_type,
        headers=headers
    )


@router.delete(
    "/{document_id}",
    status_code=status.HTTP_200_OK,
    summary="Delete a document",
    description="Permanently deletes document metadata from MongoDB and deletes the physical file from server storage."
)
async def delete_document(
    document_id: str,
    current_user: UserResponse = Depends(get_current_user)
):
    """
    Deletes document record and file on disk, ensuring current_user is the owner.
    """
    await document_service.delete_document(document_id, current_user.id)
    return {
        "success": True,
        "message": "Document successfully deleted.",
        "documentId": document_id
    }
