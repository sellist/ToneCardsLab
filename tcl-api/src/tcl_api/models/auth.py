"""Authentication-related DTOs."""

from pydantic import BaseModel, Field, EmailStr
from uuid import UUID


class LoginRequest(BaseModel):
    """OAuth login request."""
    email: EmailStr = Field(..., description="User's email address")
    password: str = Field(..., min_length=8, description="User's password")


class TokenResponse(BaseModel):
    """OAuth/Authentication token response."""
    access_token: str = Field(..., description="JWT access token")
    refresh_token: str | None = Field(None, description="JWT refresh token for obtaining new access tokens")
    token_type: str = Field(default="Bearer", description="Token type")
    expires_in: int = Field(..., description="Access token expiration time in seconds")


class LoginResponse(TokenResponse):
    """Login response with user information."""
    user_id: UUID = Field(..., description="UUID of the authenticated user")


class RefreshTokenRequest(BaseModel):
    """Token refresh request."""
    refresh_token: str = Field(..., description="Valid refresh token")


class LogoutRequest(BaseModel):
    """Logout request (token invalidation)."""
    token: str = Field(..., description="Access token to invalidate")

