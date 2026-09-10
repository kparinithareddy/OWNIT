from fastapi import Depends
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from typing import Optional

from app.core.security import decode_access_token
from app.core.exceptions import UnauthorizedException
from app.services.user_service import user_service, format_user_doc
from app.schemas.user import UserResponse

# Define HTTP Bearer token security scheme
security_scheme = HTTPBearer(
    scheme_name="JWT Bearer Token",
    description="Enter the JWT access token returned from /api/v1/auth/login or /api/v1/auth/signup",
    auto_error=False
)


async def get_current_user(
    credentials: Optional[HTTPAuthorizationCredentials] = Depends(security_scheme)
) -> UserResponse:
    """
    Dependency that extracts, decodes, and validates the JWT Bearer token from the Authorization header.
    Returns the authenticated UserResponse object.
    Raises UnauthorizedException if the token is missing, invalid, expired, or the user does not exist.
    """
    if credentials is None or not credentials.credentials:
        raise UnauthorizedException(
            message="Authentication required. Please provide a valid Bearer token.",
            details={"error_code": "TOKEN_MISSING"}
        )

    token = credentials.credentials
    payload = decode_access_token(token)

    user_id = payload.get("sub")
    if not user_id:
        raise UnauthorizedException(
            message="Invalid token payload: missing subject identifier.",
            details={"error_code": "MALFORMED_TOKEN"}
        )

    user_doc = await user_service.get_by_id(user_id)
    if not user_doc:
        raise UnauthorizedException(
            message="User account associated with this token no longer exists.",
            details={"error_code": "USER_NOT_FOUND"}
        )

    return format_user_doc(user_doc)
