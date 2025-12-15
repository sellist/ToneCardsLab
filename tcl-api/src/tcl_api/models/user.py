"""User-related Pydantic models."""

from pydantic import BaseModel, Field, EmailStr
from typing import Optional, List
from .common import TimestampMixin, IdResponse


class UserProfile(BaseModel):
    """User profile data."""
    user_id: str = Field(..., description="UUID of the user")
    email: EmailStr = Field(..., description="User's email address")
    name: Optional[str] = Field(None, description="User's display name")
    preferences: Optional[dict] = Field(default_factory=dict, description="User preferences/settings")


class UserProfileResponse(UserProfile, TimestampMixin):
    """User profile response with timestamps."""
    owned_decks_count: int = Field(default=0, description="Number of decks owned by user")
    shared_decks_count: int = Field(default=0, description="Number of decks shared with user")


class UpdateUserProfileRequest(BaseModel):
    """Request to update user profile."""
    name: Optional[str] = Field(None, max_length=100, description="Updated display name")
    preferences: Optional[dict] = Field(None, description="Updated user preferences")


class DeleteAccountRequest(BaseModel):
    """Request to delete user account."""
    confirmation: str = Field(..., description="Confirmation string (e.g., 'DELETE' or user email)")
    transfer_decks: bool = Field(
        default=True,
        description="Whether to transfer owned decks to viewers"
    )

