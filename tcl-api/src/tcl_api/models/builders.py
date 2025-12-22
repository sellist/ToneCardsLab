"""Response builders for consistent API responses."""

from typing import Any, Dict, Optional
from fastapi import status

from tcl_api.models.common import ApiResponse, ResponseStatus, ErrorDetail


class ApiResponseBuilder:
    """Builder for creating consistent API responses."""

    def __init__(self):
        self._status = ResponseStatus.SUCCESS
        self._status_code = status.HTTP_200_OK
        self._message = None
        self._data = None
        self._error: Optional[ErrorDetail] = None

    @classmethod
    def ok(cls):
        """Create a successful response builder."""
        return cls()

    @classmethod
    def created(cls):
        """Create a successful creation response builder."""
        builder = cls()
        builder._status_code = status.HTTP_201_CREATED
        return builder

    @classmethod
    def error(cls, status_code: int = status.HTTP_400_BAD_REQUEST):
        """Create an error response builder."""
        builder = cls()
        builder._status = ResponseStatus.ERROR
        builder._status_code = status_code
        return builder

    @classmethod
    def not_found(cls):
        """Create a not found error response builder."""
        builder = cls()
        builder._status = ResponseStatus.FAILURE
        builder._status_code = status.HTTP_404_NOT_FOUND
        return builder

    def status_code(self, code: int):
        """Set the HTTP status code."""
        self._status_code = code
        return self

    def message(self, msg: str):
        """Set the response message."""
        self._message = msg
        return self

    def data(self, data: Any):
        """Set the response data."""
        self._data = data
        return self

    def errors(self, errors: Dict[str, Any]):
        """Set error details."""
        self._error = ErrorDetail(
            code=errors.get("code", "UNKNOWN_ERROR"),
            message=errors.get("message", "An error occurred"),
            field=errors.get("field")
        )
        self._status = ResponseStatus.ERROR
        return self

    def error_detail(self, code: str, message: str, field: Optional[str] = None):
        """Set error details directly."""
        self._error = ErrorDetail(code=code, message=message, field=field)
        self._status = ResponseStatus.ERROR
        return self

    def meta(self, **kwargs):
        """Set metadata fields (deprecated - kept for backward compatibility)."""
        return self

    def build(self) -> ApiResponse:
        """Build the final API response."""
        return ApiResponse(
            status=self._status,
            data=self._data,
            error=self._error,
            message=self._message
        )

    def get_status_code(self) -> int:
        """Get the HTTP status code for FastAPI response."""
        return self._status_code
