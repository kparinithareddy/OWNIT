from fastapi import APIRouter
from app.api.v1.endpoints import health, auth, products, documents, ocr, warranties, notifications, maintenance

api_v1_router = APIRouter()

# Include feature endpoint routers
api_v1_router.include_router(health.router, tags=["Health"])
api_v1_router.include_router(auth.router, prefix="/auth", tags=["Authentication"])
api_v1_router.include_router(products.router, prefix="/products", tags=["Products"])
api_v1_router.include_router(documents.router, prefix="/documents", tags=["Documents"])
api_v1_router.include_router(ocr.router, prefix="/ocr", tags=["Receipt OCR"])
api_v1_router.include_router(warranties.router, prefix="/warranties", tags=["Warranty Management"])
api_v1_router.include_router(notifications.router, prefix="/notifications", tags=["In-App Notifications"])
api_v1_router.include_router(maintenance.router, prefix="/maintenance", tags=["Product Maintenance"])
