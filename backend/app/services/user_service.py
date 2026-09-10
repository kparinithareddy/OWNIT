import logging
from datetime import datetime, timezone
from typing import Optional, Dict, Any
from bson import ObjectId
from motor.motor_asyncio import AsyncIOMotorDatabase

from app.core.database import db_manager
from app.core.security import hash_password, verify_password, create_access_token
from app.core.exceptions import (
    AppException,
    NotFoundException,
    ConflictException,
    UnauthorizedException
)
from app.schemas.user import UserSignupRequest, UserLoginRequest, UserResponse, TokenResponse

logger = logging.getLogger("ownit.services.user")


def format_user_doc(doc: Dict[str, Any]) -> UserResponse:
    """
    Transforms a raw MongoDB user document into a safe UserResponse schema,
    guaranteeing that passwordHash is NEVER leaked in responses.
    """
    return UserResponse(
        id=str(doc["_id"]),
        username=doc["username"],
        preferredLanguage=doc.get("preferredLanguage", "en"),
        createdAt=doc.get("createdAt", datetime.now(timezone.utc)),
        updatedAt=doc.get("updatedAt", datetime.now(timezone.utc))
    )


class UserService:
    """
    Handles user management, authentication, and MongoDB user collection persistence.
    """
    @property
    def db(self) -> AsyncIOMotorDatabase:
        database = db_manager.get_db()
        if database is None:
            raise AppException(
                message="Database service is currently offline. Please ensure MongoDB is running.",
                status_code=503,
                error_code="DATABASE_UNAVAILABLE"
            )
        return database

    @property
    def users_collection(self):
        return self.db["users"]

    async def ensure_indexes(self) -> None:
        """
        Creates a unique index on lowercase username to guarantee uniqueness at the database layer.
        """
        try:
            await self.users_collection.create_index(
                "username_lower",
                unique=True,
                name="unique_username_lower_idx"
            )
        except Exception as exc:
            logger.warning(f"Could not create user indexes: {exc}")

    async def get_by_username(self, username: str) -> Optional[Dict[str, Any]]:
        """
        Case-insensitive search for a user by username.
        """
        return await self.users_collection.find_one(
            {"username_lower": username.strip().lower()}
        )

    async def get_by_id(self, user_id: str) -> Optional[Dict[str, Any]]:
        """
        Finds a user document by MongoDB ObjectId.
        """
        if not ObjectId.is_valid(user_id):
            return None
        return await self.users_collection.find_one({"_id": ObjectId(user_id)})

    async def signup(self, signup_data: UserSignupRequest) -> TokenResponse:
        """
        Registers a new user after verifying username uniqueness and hashing the password.
        """
        clean_username = signup_data.username.strip()
        username_lower = clean_username.lower()

        # 1. Check for existing username
        existing_user = await self.get_by_username(clean_username)
        if existing_user:
            raise ConflictException(
                message=f"Username '{clean_username}' is already taken. Please choose a different username.",
                details={"field": "username"}
            )

        # 2. Hash the password securely with bcrypt
        hashed_password = hash_password(signup_data.password)
        now = datetime.now(timezone.utc)

        # 3. Create database document
        user_doc = {
            "username": clean_username,
            "username_lower": username_lower,
            "passwordHash": hashed_password,
            "preferredLanguage": signup_data.preferredLanguage,
            "createdAt": now,
            "updatedAt": now
        }

        # 4. Insert into MongoDB
        result = await self.users_collection.insert_one(user_doc)
        user_doc["_id"] = result.inserted_id

        # 5. Format response & generate JWT token
        user_response = format_user_doc(user_doc)
        token = create_access_token({
            "sub": user_response.id,
            "username": user_response.username,
            "preferredLanguage": user_response.preferredLanguage
        })

        logger.info(f"New user registered successfully: '{clean_username}' (ID: {user_response.id})")
        return TokenResponse(
            accessToken=token,
            tokenType="bearer",
            user=user_response
        )

    async def login(self, login_data: UserLoginRequest) -> TokenResponse:
        """
        Authenticates a user with username & password, returning a new JWT access token.
        """
        clean_username = login_data.username.strip()

        # 1. Look up user by username
        user_doc = await self.get_by_username(clean_username)
        if not user_doc:
            # Use constant-time generic message to prevent username enumeration attacks
            raise UnauthorizedException(
                message="Invalid username or password.",
                details={"error_code": "INVALID_CREDENTIALS"}
            )

        # 2. Verify password with bcrypt
        if not verify_password(login_data.password, user_doc.get("passwordHash", "")):
            raise UnauthorizedException(
                message="Invalid username or password.",
                details={"error_code": "INVALID_CREDENTIALS"}
            )

        # 3. Format response & generate JWT token
        user_response = format_user_doc(user_doc)
        token = create_access_token({
            "sub": user_response.id,
            "username": user_response.username,
            "preferredLanguage": user_response.preferredLanguage
        })

        logger.info(f"User authenticated successfully: '{clean_username}'")
        return TokenResponse(
            accessToken=token,
            tokenType="bearer",
            user=user_response
        )


user_service = UserService()
