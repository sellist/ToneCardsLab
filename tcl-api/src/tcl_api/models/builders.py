"""Response builders for consistent API responses."""

from typing import Any, Dict
from fastapi import status

from tcl_api.models.response import ApiResponse, Metadata


class ApiResponseBuilder:
    """Builder for creating consistent API responses."""

    def __init__(self):
        self._success = True
        self._status_code = status.HTTP_200_OK
        self._message = None
        self._data = None
        self._errors = None
        self._metadata = Metadata.model_validate({})

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
        builder._success = False
        builder._status_code = status_code
        return builder

    @classmethod
    def not_found(cls):
        """Create a not found error response builder."""
        builder = cls()
        builder._success = False
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
        self._errors = errors
        self._success = False
        return self

    def meta(self, **kwargs):
        """Set metadata fields."""
        for key, value in kwargs.items():
            if hasattr(self._metadata, key):
                setattr(self._metadata, key, value)
        return self

    def build(self) -> ApiResponse:
        """Build the final API response."""
        return ApiResponse(
            success=self._success,
            message=self._message,
            data=self._data,
            metadata=self._metadata,
            errors=self._errors
        )

    def get_status_code(self) -> int:
        """Get the HTTP status code for FastAPI response."""
        return self._status_code
