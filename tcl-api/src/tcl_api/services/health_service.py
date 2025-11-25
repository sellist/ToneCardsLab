from tcl_api.models.health import HealthCheckResponse
from tcl_api.config import settings


class HealthService:
    def check_health(self) -> HealthCheckResponse:
        return HealthCheckResponse(
            status="healthy",
            version=settings.app_version,
            message="Service is running"
        )


health_service = HealthService()
