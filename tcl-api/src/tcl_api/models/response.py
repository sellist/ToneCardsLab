from typing import Generic, TypeVar, Optional, Dict, Any
from datetime import datetime, timezone
from pydantic import Field

from pydantic import BaseModel
import time

T = TypeVar('T')

_START_TIME = time.monotonic()


class Metadata(BaseModel):
    timestamp: datetime = Field(default_factory=lambda: datetime.now(timezone.utc), description="Response timestamp")
    request_id: Optional[str] = Field(None, description="Unique request identifier")
    version: str = Field("1.0", description="API version")
    total_count: Optional[int] = Field(None, description="Total number of items (for paginated responses)")
    page: Optional[int] = Field(None, description="Current page number")
    page_size: Optional[int] = Field(None, description="Number of items per page")
    execution_time_ms: Optional[float] = Field(None, description="Request execution time in milliseconds")


class ApiResponse(BaseModel, Generic[T]):
    success: bool = Field(True, description="Indicates if the request was successful")
    message: Optional[str] = Field(None, description="Response message or error description")
    data: Optional[T] = Field(None, description="Response payload")
    metadata: Metadata = Field(default_factory=Metadata, description="Response metadata")
    errors: Optional[Dict[str, Any]] = Field(None, description="Error details if any")

    class Config:
        json_encoders = {
            datetime: lambda v: v.isoformat()
        }


class ErrorResponse(BaseModel):
    success: bool = Field(False, description="Always false for error responses")
    message: str = Field(..., description="Error message")
    error_code: Optional[str] = Field(None, description="Specific error code")
    details: Optional[Dict[str, Any]] = Field(None, description="Additional error details")
    metadata: Metadata = Field(default_factory=Metadata, description="Response metadata")


class PaginatedResponse(BaseModel, Generic[T]):
    success: bool = Field(True, description="Indicates if the request was successful")
    message: Optional[str] = Field(None, description="Response message")
    data: list[T] = Field(default_factory=list, description="List of items")
    metadata: Metadata = Field(default_factory=Metadata, description="Response metadata with pagination info")

    def set_pagination(self, total: int, page: int, page_size: int) -> None:
        self.metadata.total_count = total
        self.metadata.page = page
        self.metadata.page_size = page_size


class HealthResponse(BaseModel):
    status: str
    version: str
    uptime_seconds: float = 0.0
    checks: dict = {}

    def __init__(self, **data):
        super().__init__()
        self.uptime_seconds = time.monotonic() - _START_TIME
