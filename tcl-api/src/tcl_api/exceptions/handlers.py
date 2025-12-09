from fastapi import FastAPI, Request, HTTPException
from fastapi.responses import JSONResponse
from tcl_api.config import get_logger, log_exception

logger = get_logger("exceptions")


async def global_exception_handler(request: Request, exc: Exception):
    log_exception(logger, exc, f"Unhandled exception in {request.method} {request.url.path}")
    return JSONResponse(
        status_code=500,
        content={
            "detail": "Internal server error",
            "message": "An unexpected error occurred"
        }
    )


async def http_exception_handler(request: Request, exc: HTTPException):
    logger.warning(f"HTTP exception in {request.method} {request.url.path}: {exc.status_code} - {exc.detail}")
    return JSONResponse(
        status_code=exc.status_code,
        content={"detail": exc.detail}
    )


def setup_exception_handlers(app: FastAPI) -> None:
    app.add_exception_handler(Exception, global_exception_handler)
    app.add_exception_handler(HTTPException, http_exception_handler)
    logger.info("Exception handlers configured")
