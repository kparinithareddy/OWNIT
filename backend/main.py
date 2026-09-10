import uvicorn
from app.main import app
from app.core.config import settings

# Export app for uvicorn CLI commands (e.g. uvicorn main:app --reload)
__all__ = ["app"]

if __name__ == "__main__":
    uvicorn.run(
        "app.main:app",
        host=settings.HOST,
        port=settings.PORT,
        reload=settings.DEBUG
    )
