import uuid
from fastapi import APIRouter
from tcl_api.models import HealthResponse, ApiResponse
from tcl_api.services.health import health_service
from tcl_api.config import get_logger

router = APIRouter(prefix="/health", tags=["health"])
logger = get_logger("controllers.health")

HealthApiResponse = ApiResponse[HealthResponse]


@router.get("", response_model=ApiResponse[HealthResponse])
def health_check() -> "ApiResponse[HealthResponse]":
    request_id = str(uuid.uuid4())
    logger.info(f"Health check endpoint accessed [request_id: {request_id}]")

    result = health_service.check_health()
    result.metadata.request_id = request_id
    logger.debug(
        f"Health check result: success={result.success}, status={result.data.status if result.data else 'unknown'} [request_id: {request_id}]")
    return result
