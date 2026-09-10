import logging
from typing import Optional, Dict, Any
from motor.motor_asyncio import AsyncIOMotorClient, AsyncIOMotorDatabase
from pymongo.errors import ConnectionFailure, ServerSelectionTimeoutError, PyMongoError

from app.core.config import settings

logger = logging.getLogger("ownit.database")


class DatabaseManager:
    """
    Manages MongoDB client and database connection lifecycle.
    Uses Motor (asynchronous Python driver for MongoDB).
    """
    def __init__(self):
        self.client: Optional[AsyncIOMotorClient] = None
        self.db: Optional[AsyncIOMotorDatabase] = None
        self.is_connected: bool = False
        self.last_error: Optional[str] = None

    async def connect(self) -> bool:
        """
        Initializes Motor client and performs a ping check to verify database connectivity.
        Does not crash the application if MongoDB is unreachable; logs a clear warning.
        """
        logger.info(f"Connecting to MongoDB at: {settings.MONGODB_URI} (DB: {settings.MONGODB_DB_NAME})")
        try:
            self.client = AsyncIOMotorClient(
                settings.MONGODB_URI,
                serverSelectionTimeoutMS=settings.MONGODB_TIMEOUT_MS,
                maxPoolSize=settings.MONGODB_MAX_POOL_SIZE,
                minPoolSize=settings.MONGODB_MIN_POOL_SIZE
            )
            self.db = self.client[settings.MONGODB_DB_NAME]

            # Verify connection with ping
            await self.client.admin.command("ping")
            self.is_connected = True
            self.last_error = None
            logger.info(f" Successfully connected to MongoDB database: '{settings.MONGODB_DB_NAME}'")
            return True

        except (ConnectionFailure, ServerSelectionTimeoutError) as exc:
            self.is_connected = False
            self.last_error = f"Connection timeout: {str(exc)}"
            logger.warning(
                f" MongoDB is unavailable at {settings.MONGODB_URI}. "
                f"The server is running, but database features will be offline until MongoDB is started."
            )
            return False

        except PyMongoError as exc:
            self.is_connected = False
            self.last_error = f"Driver error: {str(exc)}"
            logger.error(f"❌ MongoDB error: {str(exc)}")
            return False

        except Exception as exc:
            self.is_connected = False
            self.last_error = f"Unexpected error: {str(exc)}"
            logger.error(f"❌ Unexpected error connecting to MongoDB: {str(exc)}")
            return False

    async def disconnect(self) -> None:
        """
        Gracefully closes active MongoDB client connections on server shutdown.
        """
        if self.client is not None:
            logger.info("Closing MongoDB connections...")
            self.client.close()
            self.is_connected = False
            logger.info("MongoDB connection closed.")

    async def ping(self) -> Dict[str, Any]:
        """
        Performs a dynamic ping check to inspect current database health.
        """
        if self.client is None:
            # Attempt reconnection if client was never initialized
            await self.connect()

        try:
            if self.client is not None:
                await self.client.admin.command("ping")
                self.is_connected = True
                self.last_error = None
                return {
                    "status": "connected",
                    "database": settings.MONGODB_DB_NAME,
                    "uri": settings.MONGODB_URI
                }
        except Exception as exc:
            self.is_connected = False
            self.last_error = str(exc)

        return {
            "status": "disconnected",
            "database": settings.MONGODB_DB_NAME,
            "error": self.last_error or "Unable to reach MongoDB server"
        }

    def get_db(self) -> Optional[AsyncIOMotorDatabase]:
        """
        Returns the active MongoDB database instance.
        """
        return self.db

    def get_collection(self, collection_name: str):
        """
        Returns a MongoDB collection from the active database.
        """
        if self.db is not None:
            return self.db[collection_name]
        return None



# Global singleton instance
db_manager = DatabaseManager()


def get_database() -> Optional[AsyncIOMotorDatabase]:
    """
    FastAPI dependency for accessing the database.
    """
    return db_manager.get_db()
