from fastapi import APIRouter, Depends, status
from app.schemas.user import (
    UserSignupRequest,
    UserLoginRequest,
    UserPreferencesUpdate,
    UserResponse,
    TokenResponse
)
from app.services.user_service import user_service
from app.api.dependencies import get_current_user

router = APIRouter()


@router.post(
    "/signup",
    response_model=TokenResponse,
    status_code=status.HTTP_201_CREATED,
    summary="User Registration",
    description="Registers a new user account with unique username, hashed password, and preferred language."
)
async def signup(signup_data: UserSignupRequest) -> TokenResponse:
    """
    Registers a new user, saves their profile to MongoDB, and returns an access token with user details.
    """
    return await user_service.signup(signup_data)


@router.post(
    "/login",
    response_model=TokenResponse,
    status_code=status.HTTP_200_OK,
    summary="User Login",
    description="Authenticates username and password against bcrypt hash and issues a JWT access token."
)
async def login(login_data: UserLoginRequest) -> TokenResponse:
    """
    Authenticates existing user and generates an access token.
    """
    return await user_service.login(login_data)


@router.get(
    "/me",
    response_model=UserResponse,
    status_code=status.HTTP_200_OK,
    summary="Get Current User Profile",
    description="Protected endpoint returning the profile of the currently authenticated user."
)
async def get_current_user_profile(
    current_user: UserResponse = Depends(get_current_user)
) -> UserResponse:
    """
    Returns the profile information for the authenticated token owner.
    """
    return current_user


@router.patch(
    "/preferences",
    response_model=UserResponse,
    status_code=status.HTTP_200_OK,
    summary="Update User Preferences",
    description="Updates user preferences such as preferred UI/AI language (en, hi, te)."
)
async def update_user_preferences(
    prefs: UserPreferencesUpdate,
    current_user: UserResponse = Depends(get_current_user)
) -> UserResponse:
    """
    Updates the authenticated user's preferences in MongoDB.
    """
    return await user_service.update_preferences(current_user.id, prefs)


@router.post(
    "/logout",
    status_code=status.HTTP_200_OK,
    summary="User Logout",
    description="Terminates the user's active session and confirms client-side token discard."
)
async def logout(
    current_user: UserResponse = Depends(get_current_user)
):
    """
    Validates token ownership and acknowledges session logout.
    """
    return {"message": "Logged out successfully", "userId": current_user.id}

