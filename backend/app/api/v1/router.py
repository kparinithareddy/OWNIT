from fastapi import APIRouter
from app.api.v1.endpoints import health, auth, products, documents

api_v1_router = APIRouter()

# Include feature endpoint routers
api_v1_router.include_router(health.router, tags=["Health"])
api_v1_router.include_router(auth.router, prefix="/auth", tags=["Authentication"])
api_v1_router.include_router(products.router, prefix="/products", tags=["Products"])
api_v1_router.include_router(documents.router, prefix="/documents", tags=["Documents"])
