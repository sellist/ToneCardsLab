from typing import Any, Dict, Generic, Optional, TypeVar
from pydantic import BaseModel


T = TypeVar("T")

class ApiResponse(BaseModel, Generic[T]):
    success: bool = True
    code: int = 200
    message: Optional[str] = None
    meta: Optional[Dict[str, Any]] = None
    data: Optional[T] = None

    def __init__(self, **data: Any):
        super().__init__(**data)


class ResponseBuilder(Generic[T]):
    def __init__(self, data: Optional[T] = None):
        self._data: Optional[T] = data
        self._meta: Optional[Dict[str, Any]] = None
        self._success: bool = True
        self._code: int = 200
        self._message: Optional[str] = None

    def with_meta(self, meta: Dict[str, Any]) -> "ResponseBuilder[T]":
        self._meta = meta
        return self

    def with_success(self, success: bool) -> "ResponseBuilder[T]":
        self._success = success
        return self

    def with_code(self, code: int) -> "ResponseBuilder[T]":
        self._code = code
        return self

    def with_message(self, message: str) -> "ResponseBuilder[T]":
        self._message = message
        return self

    def build(self) -> ApiResponse[T]:
        return ApiResponse[T](
            success=self._success,
            code=self._code,
            message=self._message,
            meta=self._meta,
            data=self._data,
        )