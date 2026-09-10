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

    # Future integration settings (Kept safe in environment)
    MONGODB_URI: str = "mongodb://localhost:27017"
    MONGODB_DB_NAME: str = "ownit_db"
    JWT_SECRET_KEY: str = "insecure_dev_key_must_be_set_in_env_for_production"
    JWT_ALGORITHM: str = "HS256"
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 1440

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


# Global settings instance
settings = Settings()
