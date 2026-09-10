import logging
from contextlib import asynccontextmanager
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.core.config import settings
from app.core.database import db_manager
from app.core.handlers import register_exception_handlers
from app.core.scheduler import notification_scheduler
from app.api.v1.router import api_v1_router
from app.services.user_service import user_service
from app.services.product_service import product_service
from app.services.document_service import document_service
from app.services.warranty_service import warranty_service
from app.services.notification_service import notification_service
from app.services.timeline_service import timeline_service

# Configure basic logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(name)s: %(message)s"
)
logger = logging.getLogger("ownit.main")


@asynccontextmanager
async def lifespan(app: FastAPI):
    """
    Manages the application lifecycle:
    - Connects to MongoDB on startup
    - Ensures database indexes (users, products, documents, warranties, notifications, timeline)
    - Starts the local development background notification scheduler
    - Gracefully stops scheduler and disconnects MongoDB on shutdown
    """
    logger.info(f"Starting {settings.PROJECT_NAME} v{settings.VERSION}...")
    # 1. Initialize MongoDB connection
    is_connected = await db_manager.connect()

    # 2. Ensure indexes and start scheduler if database is reachable
    if is_connected:
        await user_service.ensure_indexes()
        await product_service.ensure_indexes()
        await document_service.ensure_indexes()
        await warranty_service.ensure_indexes()
        await notification_service.ensure_indexes()
        await timeline_service.ensure_indexes()
        # Start notification scheduler
        notification_scheduler.start()


    yield

    # 3. Shutdown logic
    logger.info(f"Shutting down {settings.PROJECT_NAME}...")
    notification_scheduler.stop()
    await db_manager.disconnect()


def create_app() -> FastAPI:
    """
    Application factory initializing and configuring the FastAPI instance.
    """
    app = FastAPI(
        title=settings.PROJECT_NAME,
        description=f"{settings.PROJECT_TAGLINE} — Smart Product Lifecycle Assistant Backend API",
        version=settings.VERSION,
        docs_url="/docs",
        redoc_url="/redoc",
        openapi_url="/openapi.json",
        lifespan=lifespan
    )

    # 1. Configure CORS middleware for local frontend development
    app.add_middleware(
        CORSMiddleware,
        allow_origins=settings.cors_origins,
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )

    # 2. Register global exception handlers for unified error formats
    register_exception_handlers(app)

    # 3. Mount versioned API routes (/api/v1)
    app.include_router(api_v1_router, prefix=settings.API_V1_PREFIX)

    # 4. Root welcoming route
    @app.get("/", tags=["Root"])
    async def root():
        return {
            "message": f"Welcome to {settings.PROJECT_NAME} API",
            "tagline": settings.PROJECT_TAGLINE,
            "version": settings.VERSION,
            "docs": "/docs",
            "health_v1": f"{settings.API_V1_PREFIX}/health",
            "auth_v1": f"{settings.API_V1_PREFIX}/auth",
            "products_v1": f"{settings.API_V1_PREFIX}/products",
            "documents_v1": f"{settings.API_V1_PREFIX}/documents",
            "warranties_v1": f"{settings.API_V1_PREFIX}/warranties",
            "notifications_v1": f"{settings.API_V1_PREFIX}/notifications"
        }

    return app


app = create_app()
