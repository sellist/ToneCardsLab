from pydantic import BaseModel
import time

_START_TIME = time.monotonic()


class HealthResponse(BaseModel):
    status: str
    version: str
    uptime_seconds: float = 0.0
    checks: dict = {}

    def __init__(self, **data):
        super().__init__()
        self.uptime_seconds = time.monotonic() - _START_TIME
