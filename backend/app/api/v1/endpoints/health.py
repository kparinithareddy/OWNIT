from typing import Optional, Dict, Any
from fastapi import APIRouter
from pydantic import BaseModel

from app.core.database import db_manager

router = APIRouter()


class DatabaseHealth(BaseModel):
    status: str
    database: str
    uri: Optional[str] = None
    error: Optional[str] = None


class HealthResponse(BaseModel):
    status: str
    application: str
    database: Optional[str] = "unknown"


@router.get(
    "/health",
    response_model=HealthResponse,
    summary="Application Health Check",
    description="Returns the operational health status of the OWNIT backend service and database connectivity."
)
async def get_health() -> HealthResponse:
    """
    Standard application health check endpoint.
    """
    db_status = "connected" if db_manager.is_connected else "disconnected"
    return HealthResponse(
        status="ok",
        application="OWNIT",
        database=db_status
    )


@router.get(
    "/health/db",
    response_model=DatabaseHealth,
    summary="Database Health Check",
    description="Performs an active ping check against the MongoDB server and returns detailed connection state."
)
async def get_db_health() -> DatabaseHealth:
    """
    Active database ping and diagnostics endpoint.
    """
    ping_result = await db_manager.ping()
    return DatabaseHealth(**ping_result)
