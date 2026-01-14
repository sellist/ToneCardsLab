"""Common reusable Pydantic models for API responses and requests."""

from pydantic import BaseModel, Field
from typing import Optional
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

