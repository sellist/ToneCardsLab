import time
from fastapi import Request
from fastapi.responses import Response
from tcl_api.config import get_logger

logger = get_logger("middleware.logging")


class LoggingMiddleware:

    def __init__(self, app):
        self.app = app

    async def __call__(self, request: Request, call_next):
        start_time = time.time()

        logger.info(
            f"Incoming request: {request.method} {request.url.path} "
            f"from {request.client.host if request.client else 'unknown'}"
        )

        if request.query_params:
            logger.debug(f"Query parameters: {dict(request.query_params)}")

        logger.debug(f"Request headers: {dict(request.headers)}")

        response = await call_next(request)

        process_time = time.time() - start_time

        logger.info(
            f"Response: {request.method} {request.url.path} "
            f"-> {response.status_code} ({process_time:.4f}s)"
        )

        response.headers["X-Process-Time"] = str(process_time)

        return response