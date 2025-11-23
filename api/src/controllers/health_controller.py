from fastapi import APIRouter
from src.services.health_service import HealthService

router = APIRouter(tags=["health"])


@router.get("/healthcheck")
def health_check():
    return HealthService.get_health_status()

