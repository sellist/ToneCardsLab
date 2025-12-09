from tcl_api.models.health import HealthData
from tcl_api.config import settings, get_logger


class HealthService:
    def __init__(self):
        self.logger = get_logger("services.health")

    def check_health(self) -> HealthData:
        self.logger.debug("Performing health check")
        response = HealthData(
            status="healthy",
            version=settings.APP_VERSION
        )
        self.logger.info("Health check completed successfully")
        return response


health_service = HealthService()
