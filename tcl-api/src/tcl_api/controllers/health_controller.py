from fastapi import APIRouter
from tcl_api.models.health import HealthCheckResponse
from tcl_api.services.health_service import health_service

router = APIRouter(prefix="/health", tags=["health"])


@router.get("", response_model=HealthCheckResponse)
def health_check() -> HealthCheckResponse:
    return health_service.check_health()

