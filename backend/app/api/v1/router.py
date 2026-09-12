from fastapi import APIRouter
from app.api.v1.endpoints import (
    health,
    auth,
    products,
    documents,
    ocr,
    warranties,
    notifications,
    maintenance,
    ai,
    warranty_intelligence,
    claim_assistant,
    service_history,
    accessories,
    safety_recalls,
    translation
)

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
api_v1_router.include_router(service_history.router, prefix="/services", tags=["Service History"])
api_v1_router.include_router(accessories.router, prefix="/accessories", tags=["Accessories & Compatibility"])
api_v1_router.include_router(safety_recalls.router, prefix="/safety-recalls", tags=["Safety Recalls & Bulletins"])
api_v1_router.include_router(ai.router, prefix="/ai", tags=["Local AI (Ollama)"])
api_v1_router.include_router(warranty_intelligence.router, prefix="/warranty-intelligence", tags=["Warranty Intelligence"])
api_v1_router.include_router(claim_assistant.router, prefix="/claim-assistant", tags=["Warranty Claim Assistant"])
api_v1_router.include_router(translation.router, prefix="/translation", tags=["Translation & Localization"])





