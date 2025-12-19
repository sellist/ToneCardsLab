"""Common reusable Pydantic models for API responses and requests."""

from pydantic import BaseModel, Field, ConfigDict
from typing import Optional, Generic, TypeVar, List
from datetime import datetime
from enum import Enum


class ResponseStatus(str, Enum):
    """Standard response status values."""
    SUCCESS = "success"
    FAILURE = "failure"
    ERROR = "error"


class ErrorDetail(BaseModel):
    """Detailed error information."""
    code: str = Field(..., description="Error code for programmatic handling")
    message: str = Field(..., description="Human-readable error message")
    field: Optional[str] = Field(None, description="Field name if error is field-specific")


T = TypeVar('T')


class ApiResponse(BaseModel, Generic[T]):
    """Generic API response wrapper for consistent response structure."""
    status: ResponseStatus = Field(..., description="Response status")
    data: Optional[T] = Field(None, description="Response data payload")
    error: Optional[ErrorDetail] = Field(None, description="Error details if status is failure/error")
    message: Optional[str] = Field(None, description="Optional human-readable message")

    model_config = ConfigDict(json_schema_extra={
        "examples": [
            {
                "status": "success",
                "data": {"id": "123"},
                "message": "Operation completed successfully"
            }
        ]
    })


class PaginationParams(BaseModel):
    """Common pagination parameters for list endpoints."""
    page: int = Field(default=1, ge=1, description="Page number (1-indexed)")
    page_size: int = Field(default=20, ge=1, le=100, description="Number of items per page")
    sort_order: Optional[str] = Field(default="created_desc", description="Sort order (e.g., created_desc, title_asc)")


class PaginatedResponse(BaseModel, Generic[T]):
    """Generic paginated response wrapper."""
    items: List[T] = Field(..., description="List of items for current page")
    total_count: int = Field(..., description="Total number of items across all pages")
    page: int = Field(..., description="Current page number")
    page_size: int = Field(..., description="Number of items per page")
    total_pages: int = Field(..., description="Total number of pages")

    model_config = ConfigDict(json_schema_extra={
        "examples": [
            {
                "items": [],
                "total_count": 100,
                "page": 1,
                "page_size": 20,
                "total_pages": 5
            }
        ]
    })


class TokenResponse(BaseModel):
    """OAuth/Authentication token response."""
    access_token: str = Field(..., description="JWT access token")
    refresh_token: Optional[str] = Field(None, description="JWT refresh token for obtaining new access tokens")
    token_type: str = Field(default="Bearer", description="Token type")
    expires_in: int = Field(..., description="Access token expiration time in seconds")


class TimestampMixin(BaseModel):
    """Mixin for models with timestamp fields."""
    created_at: datetime = Field(..., description="Timestamp when resource was created")
    updated_at: datetime = Field(..., description="Timestamp when resource was last updated")


class OwnershipMixin(BaseModel):
    """Mixin for models with ownership fields."""
    owner_id: str = Field(..., description="UUID of the user who owns this resource")
    is_public: bool = Field(default=False, description="Whether this resource is publicly accessible")


class IdResponse(BaseModel):
    """Response containing a single resource ID."""
    id: str = Field(..., description="UUID of the resource")


class SearchParams(BaseModel):
    """Common search parameters."""
    query: str = Field(..., min_length=1, description="Search query string")
    page: int = Field(default=1, ge=1, description="Page number")
    page_size: int = Field(default=20, ge=1, le=100, description="Items per page")


class ReportRequest(BaseModel):
    """Request model for reporting inappropriate content."""
    deck_id: str = Field(..., description="UUID of the deck being reported")
    reason: str = Field(..., description="Category/reason for the report")
    description: Optional[str] = Field(None, max_length=1000, description="Additional details about the report")
