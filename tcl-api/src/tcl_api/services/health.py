from tcl_api.models.response import ApiResponse, HealthResponse
from tcl_api.config import settings, get_logger


class HealthService:
    def __init__(self):
        self.logger = get_logger("services.health")

    def check_health(self) -> ApiResponse[HealthResponse]:
        self.logger.debug("Performing health check")
        health_data = HealthResponse(
            status="healthy",
            version=settings.APP_VERSION
        )
        response = ApiResponse(
            success=True,
            data=health_data,
            message="Service is healthy"
        )
        self.logger.info("Health check completed successfully")
        return response


health_service = HealthService()
