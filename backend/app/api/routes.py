from fastapi import APIRouter
from app.core.config import settings

api_router = APIRouter()


@api_router.get("/health", tags=["Health"])
async def health_check():
    """
    Health check endpoint to verify backend service status.
    """
    return {
        "status": "healthy",
        "project": settings.PROJECT_NAME,
        "tagline": settings.PROJECT_TAGLINE,
        "version": settings.VERSION,
        "environment": settings.ENVIRONMENT
    }
