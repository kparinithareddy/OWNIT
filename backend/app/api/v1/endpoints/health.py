from fastapi import APIRouter
from pydantic import BaseModel

router = APIRouter()


class HealthResponse(BaseModel):
    status: str
    application: str


@router.get(
    "/health",
    response_model=HealthResponse,
    summary="Health Check Endpoint",
    description="Returns the operational health status of the OWNIT backend service."
)
async def get_health() -> HealthResponse:
    """
    Health check endpoint returning system status.
    """
    return HealthResponse(
        status="ok",
        application="OWNIT"
    )
