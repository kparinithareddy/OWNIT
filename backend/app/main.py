import logging
from contextlib import asynccontextmanager
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.core.config import settings
from app.core.database import db_manager
from app.core.handlers import register_exception_handlers
from app.api.v1.router import api_v1_router

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
    - Connects to MongoDB on startup without crashing if offline
    - Gracefully disconnects MongoDB on shutdown
    """
    logger.info(f"Starting {settings.PROJECT_NAME} v{settings.VERSION}...")
    # Initialize MongoDB connection
    await db_manager.connect()

    yield

    # Shutdown logic
    logger.info(f"Shutting down {settings.PROJECT_NAME}...")
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
            "db_health_v1": f"{settings.API_V1_PREFIX}/health/db"
        }

    return app


app = create_app()
