from typing import TypeVar, Generic, Optional, Any, Dict
from fastapi import APIRouter
from tcl_api.models import ApiResponse
from tcl_api.config import get_logger

T = TypeVar('T')


class BaseController(Generic[T]):
    def __init__(self, prefix: str, tags: list[str], controller_name: str):
        self.router = APIRouter(prefix=prefix, tags=tags)
        self.logger = get_logger(f"controllers.{controller_name}")
        self._register_routes()

    def _register_routes(self):
        pass

    def build_success_response(self, data: T, message: Optional[str] = None) -> ApiResponse[T]:
        return ApiResponse(
            success=True,
            data=data,
            message=message
        )

    def build_error_response(self, message: str, errors: Optional[Dict[str, Any]] = None) -> ApiResponse[None]:
        response_kwargs = {
            "success": False,
            "message": message,
            "data": None
        }
        if errors is not None:
            response_kwargs["errors"] = errors
        return ApiResponse(**response_kwargs)
