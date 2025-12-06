from tcl_api.models.health import HealthCheckResponse
from tcl_api.config import settings, get_logger


class HealthService:
    def __init__(self):
        self.logger = get_logger("services.health")

    def check_health(self) -> HealthCheckResponse:
        self.logger.debug("Performing health check")
        response = HealthCheckResponse(
            status="healthy",
            version=settings.app_version,
            message="Service is running"
        )
        self.logger.info("Health check completed successfully")
        return response


health_service = HealthService()
