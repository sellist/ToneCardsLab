from fastapi import APIRouter
from tcl_api.models.health import HealthCheckResponse
from tcl_api.services.health_service import health_service
from tcl_api.config import get_logger

router = APIRouter(prefix="/health", tags=["health"])
logger = get_logger("controllers.health")


@router.get("", response_model=HealthCheckResponse)
def health_check() -> HealthCheckResponse:
    logger.info("Health check endpoint accessed")
    result = health_service.check_health()
    logger.debug(f"Health check result: {result}")
    return result

