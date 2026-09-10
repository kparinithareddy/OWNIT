from fastapi import APIRouter
from app.api.v1.endpoints import health

api_v1_router = APIRouter()

# Include feature endpoint routers
api_v1_router.include_router(health.router, tags=["Health"])
