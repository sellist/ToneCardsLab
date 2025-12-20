from tcl_api.models.health import HealthResponse
from tcl_api.config import settings, get_logger


class HealthService:
    def __init__(self):
        self.logger = get_logger("services.health")

    def check_health(self) -> HealthResponse:
        self.logger.debug("Performing health check")
        response = HealthResponse(
            status="healthy",
            version=settings.APP_VERSION
        )
        self.logger.info("Health check completed successfully")
        return response


health_service = HealthService()
