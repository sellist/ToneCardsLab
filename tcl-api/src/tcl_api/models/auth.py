"""Authentication-related Pydantic models."""

from pydantic import BaseModel, Field, EmailStr
from .common import TokenResponse


class LoginRequest(BaseModel):
    """OAuth login request."""
    email: EmailStr = Field(..., description="User's email address")
    password: str = Field(..., min_length=8, description="User's password")


class LoginResponse(TokenResponse):
    """Login response with user information."""
    user_id: str = Field(..., description="UUID of the authenticated user")


class RefreshTokenRequest(BaseModel):
    """Token refresh request."""
    refresh_token: str = Field(..., description="Valid refresh token")


class LogoutRequest(BaseModel):
    """Logout request (token invalidation)."""
    token: str = Field(..., description="Access token to invalidate")

