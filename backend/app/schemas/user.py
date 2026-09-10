from pydantic import BaseModel, Field, field_validator, model_validator
from datetime import datetime
from typing import Optional, Literal
import re


class UserSignupRequest(BaseModel):
    username: str = Field(
        ...,
        min_length=3,
        max_length=30,
        description="Unique username containing letters, numbers, and underscores"
    )
    password: str = Field(
        ...,
        min_length=8,
        max_length=128,
        description="Secure password, minimum 8 characters"
    )
    confirmPassword: str = Field(
        ...,
        description="Password confirmation, must match password exactly"
    )
    preferredLanguage: Literal["en", "hi", "te"] = Field(
        default="en",
        description="Preferred UI language: en (English), hi (Hindi), te (Telugu)"
    )

    @field_validator("username")
    @classmethod
    def validate_username_format(cls, v: str) -> str:
        clean = v.strip()
        if not re.match(r"^[a-zA-Z0-9_.-]+$", clean):
            raise ValueError("Username can only contain alphanumeric characters, dots, underscores, and dashes")
        return clean

    @model_validator(mode="after")
    def validate_passwords_match(self):
        if self.password != self.confirmPassword:
            raise ValueError("Passwords do not match. Please ensure 'password' and 'confirmPassword' are identical.")
        return self


class UserLoginRequest(BaseModel):
    username: str = Field(..., description="Your registered username")
    password: str = Field(..., description="Your secret password")

    @field_validator("username")
    @classmethod
    def strip_username(cls, v: str) -> str:
        return v.strip()


class UserPreferencesUpdate(BaseModel):
    preferredLanguage: Literal["en", "hi", "te"] = Field(
        ...,
        description="Preferred UI and assistant language: en (English), hi (Hindi), te (Telugu)"
    )



class UserResponse(BaseModel):
    id: str = Field(..., description="Unique user identifier")
    username: str = Field(..., description="User account name")
    preferredLanguage: str = Field(default="en", description="Preferred display language")
    createdAt: datetime = Field(..., description="Account creation timestamp (UTC)")
    updatedAt: datetime = Field(..., description="Account last updated timestamp (UTC)")

    model_config = {
        "from_attributes": True,
        "json_schema_extra": {
            "example": {
                "id": "66dbb01234abcd5678ef9012",
                "username": "parinitha",
                "preferredLanguage": "en",
                "createdAt": "2026-09-10T08:00:00Z",
                "updatedAt": "2026-09-10T08:00:00Z"
            }
        }
    }


class TokenResponse(BaseModel):
    accessToken: str = Field(..., description="JWT Bearer access token")
    tokenType: str = Field(default="bearer", description="Token authentication scheme")
    user: UserResponse = Field(..., description="Authenticated user profile details")
