from datetime import datetime
from typing import Dict, Any


class HealthService:
    @staticmethod
    def get_health_status() -> Dict[str, Any]:
        return {
            "status": "healthy",
            "timestamp": datetime.utcnow().isoformat(),
            "service": "ToneCards API",
        }

