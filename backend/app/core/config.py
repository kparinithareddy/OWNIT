import os
from pydantic_settings import BaseSettings, SettingsConfigDict
from typing import List


class Settings(BaseSettings):
    """
    Application Settings loaded and validated from environment variables or .env file.
    Follows 12-factor application design principles for secure configurations.
    """
    PROJECT_NAME: str = "OWNIT"
    PROJECT_TAGLINE: str = "Own More. Worry Less."
    VERSION: str = "0.1.0"
    API_V1_PREFIX: str = "/api/v1"
    
    # Server configuration
    ENVIRONMENT: str = "development"
    HOST: str = "127.0.0.1"
    PORT: int = 8000
    DEBUG: bool = True
    
    # CORS Configuration (Allowed origins for frontend clients)
    ALLOWED_ORIGINS: str = "http://localhost:5173,http://127.0.0.1:5173,http://localhost:3000"

    # MongoDB Configuration
    MONGODB_URI: str = "mongodb://localhost:27017"
    MONGODB_DB_NAME: str = "OWNIT"
    MONGODB_TIMEOUT_MS: int = 3000
    MONGODB_MAX_POOL_SIZE: int = 10
    MONGODB_MIN_POOL_SIZE: int = 1

    # Security & Authentication
    JWT_SECRET_KEY: str = "insecure_dev_key_must_be_set_in_env_for_production"
    JWT_ALGORITHM: str = "HS256"
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 1440

    # Document Upload & Storage Settings
    UPLOAD_DIR: str = "uploads/documents"
    MAX_UPLOAD_SIZE_BYTES: int = 10 * 1024 * 1024  # 10 MB limit
    ALLOWED_MIME_TYPES: List[str] = [
        "application/pdf",
        "image/jpeg",
        "image/png",
        "image/webp",
        "image/gif",
        "application/vnd.openxmlformats-officedocument.wordprocessingml.document",
        "application/msword",
        "application/octet-stream",
        "application/zip"
    ]
    ALLOWED_EXTENSIONS: List[str] = [
        ".pdf",
        ".jpg",
        ".jpeg",
        ".png",
        ".webp",
        ".gif",
        ".docx",
        ".doc"
    ]

    # OCR & AI Settings (Local services - Ollama LLM & Tesseract OCR)
    TESSERACT_CMD_PATH: str = r"C:\Program Files\Tesseract-OCR\tesseract.exe"
    OLLAMA_BASE_URL: str = "http://localhost:11434"
    OLLAMA_MODEL: str = "llama3.2"
    OLLAMA_TIMEOUT_SECONDS: float = 120.0

    # Google Cloud Translation Settings (Secure backend API key)
    GOOGLE_TRANSLATE_API_KEY: str = ""
    GOOGLE_TRANSLATE_TIMEOUT_SECONDS: float = 10.0


    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        extra="ignore",
        case_sensitive=False
    )

    @property
    def cors_origins(self) -> List[str]:
        """
        Parses comma-separated ALLOWED_ORIGINS string into a clean list of URLs.
        """
        return [origin.strip() for origin in self.ALLOWED_ORIGINS.split(",") if origin.strip()]

    @property
    def absolute_upload_dir(self) -> str:
        """
        Returns absolute path to upload directory.
        """
        base_dir = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
        target = os.path.join(base_dir, self.UPLOAD_DIR)
        os.makedirs(target, exist_ok=True)
        return target


# Global settings instance
settings = Settings()
