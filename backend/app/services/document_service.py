import os
import uuid
import logging
from datetime import datetime, timezone
from typing import Optional, List, Dict, Any, Tuple
from bson import ObjectId
from fastapi import UploadFile
from motor.motor_asyncio import AsyncIOMotorDatabase

from app.core.config import settings
from app.core.database import db_manager
from app.core.exceptions import (
    AppException,
    NotFoundException,
    ValidationException,
    UnauthorizedException
)
from app.schemas.document import DocumentResponse, VALID_DOCUMENT_TYPES

logger = logging.getLogger("ownit.services.document")


def format_doc_response(doc: Dict[str, Any], product_info: Optional[Dict[str, Any]] = None) -> DocumentResponse:
    """
    Transforms MongoDB document into typed DocumentResponse schema.
    """
    return DocumentResponse(
        id=str(doc["_id"]),
        userId=str(doc["userId"]),
        productId=str(doc["productId"]),
        documentType=doc["documentType"],
        originalFilename=doc["originalFilename"],
        storedFilename=doc["storedFilename"],
        mimeType=doc["mimeType"],
        fileSize=doc["fileSize"],
        uploadedAt=doc.get("uploadedAt", datetime.now(timezone.utc)),
        productName=product_info.get("name") if product_info else doc.get("productName"),
        productBrand=product_info.get("brand") if product_info else doc.get("productBrand")
    )


class DocumentService:
    """
    Manages document upload, validation, physical storage, and MongoDB persistence.
    """
    @property
    def db(self) -> AsyncIOMotorDatabase:
        database = db_manager.get_db()
        if database is None:
            raise AppException(
                message="Database service is currently offline.",
                status_code=503,
                error_code="DATABASE_UNAVAILABLE"
            )
        return database

    @property
    def collection(self):
        return self.db["documents"]

    @property
    def products_collection(self):
        return self.db["products"]

    async def ensure_indexes(self) -> None:
        """
        Creates MongoDB indexes for fast user & product document lookups.
        """
        try:
            await self.collection.create_index(
                [("userId", 1), ("createdAt", -1)],
                name="user_documents_created_idx"
            )
            await self.collection.create_index(
                [("userId", 1), ("productId", 1)],
                name="user_product_documents_idx"
            )
            await self.collection.create_index(
                [("userId", 1), ("documentType", 1)],
                name="user_document_type_idx"
            )
            logger.info(" Document indexes ensured in MongoDB.")
        except Exception as exc:
            logger.warning(f"Could not create document indexes: {exc}")

    def validate_file(self, file: UploadFile) -> Tuple[str, str]:
        """
        Validates file extension and MIME type.
        Returns clean (filename, extension).
        """
        if not file.filename:
            raise ValidationException("Uploaded file must have a valid filename.")

        filename = os.path.basename(file.filename)
        _, ext = os.path.splitext(filename)
        ext_lower = ext.lower()

        # 1. Extension check
        if ext_lower not in settings.ALLOWED_EXTENSIONS:
            allowed_ext_str = ", ".join(settings.ALLOWED_EXTENSIONS)
            raise ValidationException(
                f"File format '{ext}' is not supported. Allowed formats: {allowed_ext_str}",
                details={"allowedExtensions": settings.ALLOWED_EXTENSIONS}
            )

        # 2. Content-type check
        content_type = file.content_type or ""
        if content_type not in settings.ALLOWED_MIME_TYPES:
            # Check if extension matches expected fallback
            if ext_lower == ".pdf" and "pdf" in content_type:
                content_type = "application/pdf"
            elif ext_lower in [".jpg", ".jpeg"] and "image" in content_type:
                content_type = "image/jpeg"
            elif ext_lower == ".png" and "image" in content_type:
                content_type = "image/png"
            else:
                allowed_mimes_str = ", ".join(settings.ALLOWED_MIME_TYPES)
                raise ValidationException(
                    f"File MIME type '{content_type}' is not supported. Allowed: {allowed_mimes_str}",
                    details={"allowedMimeTypes": settings.ALLOWED_MIME_TYPES}
                )

        return filename, ext_lower, content_type

    async def upload_document(
        self,
        user_id: str,
        product_id: str,
        document_type: str,
        file: UploadFile
    ) -> DocumentResponse:
        """
        Validates ownership, saves file to storage directory, and records metadata in MongoDB.
        """
        # 1. Validate Document Type
        if document_type not in VALID_DOCUMENT_TYPES:
            valid_types_str = ", ".join(VALID_DOCUMENT_TYPES)
            raise ValidationException(
                f"Invalid document type '{document_type}'. Allowed types: {valid_types_str}",
                details={"allowedTypes": VALID_DOCUMENT_TYPES}
            )

        # 2. Verify Product Ownership
        if not ObjectId.is_valid(product_id):
            raise NotFoundException(
                message=f"Product with ID '{product_id}' was not found.",
                details={"productId": product_id}
            )

        product_doc = await self.products_collection.find_one({
            "_id": ObjectId(product_id),
            "userId": user_id
        })

        if not product_doc:
            raise NotFoundException(
                message=f"Product with ID '{product_id}' was not found or you do not have permission to attach documents to it.",
                details={"productId": product_id}
            )

        # 3. Validate File format & MIME
        original_filename, ext, mime_type = self.validate_file(file)

        # 4. Read file content & validate size limit
        file_bytes = await file.read()
        file_size = len(file_bytes)

        if file_size > settings.MAX_UPLOAD_SIZE_BYTES:
            max_mb = settings.MAX_UPLOAD_SIZE_BYTES / (1024 * 1024)
            raise ValidationException(
                f"File size ({file_size / (1024 * 1024):.2f} MB) exceeds maximum allowed limit of {max_mb:.0f} MB.",
                details={"maxSizeBytes": settings.MAX_UPLOAD_SIZE_BYTES}
            )

        if file_size == 0:
            raise ValidationException("Uploaded file is empty (0 bytes).")

        # 5. Generate unique safe stored filename
        unique_token = uuid.uuid4().hex[:12]
        stored_filename = f"{user_id[:8]}_{product_id[:8]}_{unique_token}{ext}"
        storage_path = os.path.join(settings.absolute_upload_dir, stored_filename)

        # 6. Write physical file to storage
        try:
            with open(storage_path, "wb") as f:
                f.write(file_bytes)
        except Exception as exc:
            logger.error(f"Failed to save file to disk at {storage_path}: {exc}")
            raise AppException("Failed to save uploaded file to server storage.")

        # 7. Record document metadata in MongoDB
        now = datetime.now(timezone.utc)
        doc_record = {
            "userId": user_id,
            "productId": product_id,
            "documentType": document_type,
            "originalFilename": original_filename,
            "storedFilename": stored_filename,
            "filePath": storage_path,
            "mimeType": mime_type,
            "fileSize": file_size,
            "uploadedAt": now,
            "productName": product_doc.get("name"),
            "productBrand": product_doc.get("brand")
        }

        result = await self.collection.insert_one(doc_record)
        doc_record["_id"] = result.inserted_id

        logger.info(f"Document uploaded: '{original_filename}' (ID: {doc_record['_id']}) for product {product_id} by user {user_id}")
        return format_doc_response(doc_record, product_doc)

    async def list_user_documents(
        self,
        user_id: str,
        product_id: Optional[str] = None,
        document_type: Optional[str] = None
    ) -> List[DocumentResponse]:
        """
        Retrieves all documents belonging to user with optional filters.
        """
        query: Dict[str, Any] = {"userId": user_id}

        if product_id and product_id.strip() and product_id != "All":
            query["productId"] = product_id.strip()

        if document_type and document_type.strip() and document_type != "All":
            query["documentType"] = document_type.strip()

        cursor = self.collection.find(query).sort("uploadedAt", -1)
        documents = []
        async for doc in cursor:
            documents.append(format_doc_response(doc))

        return documents

    async def get_document_by_id(self, document_id: str, user_id: str) -> Dict[str, Any]:
        """
        Retrieves document record, verifying ownership.
        """
        if not ObjectId.is_valid(document_id):
            raise NotFoundException(
                message=f"Document with ID '{document_id}' was not found.",
                details={"documentId": document_id}
            )

        doc = await self.collection.find_one({
            "_id": ObjectId(document_id),
            "userId": user_id
        })

        if not doc:
            raise NotFoundException(
                message=f"Document with ID '{document_id}' was not found or access is denied.",
                details={"documentId": document_id}
            )

        return doc

    async def get_document_response(self, document_id: str, user_id: str) -> DocumentResponse:
        doc = await self.get_document_by_id(document_id, user_id)
        return format_doc_response(doc)

    async def get_file_for_download(self, document_id: str, user_id: str) -> Tuple[str, str, str]:
        """
        Retrieves physical file path, original filename, and MIME type for serving/downloading.
        """
        doc = await self.get_document_by_id(document_id, user_id)
        file_path = doc.get("filePath")

        if not file_path or not os.path.exists(file_path):
            # Fallback check inside upload dir
            alt_path = os.path.join(settings.absolute_upload_dir, doc.get("storedFilename", ""))
            if os.path.exists(alt_path):
                file_path = alt_path
            else:
                logger.error(f"Physical file missing on disk: {file_path}")
                raise NotFoundException("Physical file not found on server disk.")

        return file_path, doc["originalFilename"], doc["mimeType"]

    async def delete_document(self, document_id: str, user_id: str) -> bool:
        """
        Deletes document from MongoDB and deletes the physical file from disk.
        """
        doc = await self.get_document_by_id(document_id, user_id)

        # 1. Delete physical file
        file_path = doc.get("filePath")
        if file_path and os.path.exists(file_path):
            try:
                os.remove(file_path)
                logger.info(f"Deleted physical file from disk: {file_path}")
            except Exception as exc:
                logger.warning(f"Could not delete physical file: {exc}")

        # 2. Delete MongoDB record
        await self.collection.delete_one({"_id": doc["_id"]})
        logger.info(f"Document deleted: ID {document_id} by user {user_id}")
        return True


document_service = DocumentService()
