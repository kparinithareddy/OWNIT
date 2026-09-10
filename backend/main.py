from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from app.core.config import settings
from app.api.routes import api_router

# Initialize FastAPI application
app = FastAPI(
    title=settings.PROJECT_NAME,
    description="Smart Product Lifecycle Assistant API",
    version=settings.VERSION,
    docs_url="/docs",
    redoc_url="/redoc"
)

# Configure Cross-Origin Resource Sharing (CORS) for frontend interaction
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.cors_origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Mount API routers
app.include_router(api_router, prefix="/api")


@app.get("/", tags=["Root"])
async def root():
    """
    Root endpoint returning basic project metadata.
    """
    return {
        "message": f"Welcome to {settings.PROJECT_NAME} API",
        "tagline": settings.PROJECT_TAGLINE,
        "docs": "/docs",
        "health": "/api/health"
    }


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(
        "main:app",
        host=settings.HOST,
        port=settings.PORT,
        reload=True
    )
