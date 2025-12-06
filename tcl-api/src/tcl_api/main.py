"""Main FastAPI application"""

from fastapi import FastAPI, Request, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from tcl_api.config import settings, setup_logging, get_logger, log_exception
from tcl_api.controllers import health_router
from tcl_api.middleware import LoggingMiddleware
from contextlib import asynccontextmanager

setup_logging()
logger = get_logger("main")


def create_app() -> FastAPI:
    logger.info("Creating FastAPI application")

    app = FastAPI(
        title=settings.app_name,
        version=settings.app_version,
        debug=settings.debug,
        description="ToneCards Lab API for managing musical language flashcards",
        docs_url="/docs",
        redoc_url="/redoc",
        openapi_url="/openapi.json"
    )

    @asynccontextmanager
    async def lifespan(app: FastAPI):
        logger.info(f"Starting {settings.app_name} v{settings.app_version}")
        logger.info(f"Debug mode: {settings.debug}")
        logger.info(f"API prefix: {settings.api_prefix}")
        logger.info(f"CORS origins: {settings.cors_origins}")

        yield

        logger.info(f"Shutting down {settings.app_name}")

    app.add_middleware(LoggingMiddleware)

    logger.info("Adding CORS middleware")
    app.add_middleware(
        CORSMiddleware,
        allow_origins=settings.cors_origins,
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )

    logger.info("Including health router")
    app.include_router(health_router, prefix=settings.api_prefix)

    @app.exception_handler(Exception)
    async def global_exception_handler(request: Request, exc: Exception):
        log_exception(logger, exc, f"Unhandled exception in {request.method} {request.url.path}")
        return JSONResponse(
            status_code=500,
            content={
                "detail": "Internal server error",
                "message": "An unexpected error occurred"
            }
        )

    @app.exception_handler(HTTPException)
    async def http_exception_handler(request: Request, exc: HTTPException):
        logger.warning(f"HTTP exception in {request.method} {request.url.path}: {exc.status_code} - {exc.detail}")
        return JSONResponse(
            status_code=exc.status_code,
            content={"detail": exc.detail}
        )

    @app.middleware("http")
    async def logging_middleware(request: Request, call_next):
        return await LoggingMiddleware(app)(request, call_next)

    logger.info("FastAPI application created successfully")
    return app



app = create_app()


@app.get("/")
def root():
    return {
        "message": "Welcome to ToneCards Lab API",
        "version": settings.app_version,
        "docs": "/docs"
    }

if __name__ == "__main__":
    setup_logging()

    import uvicorn

    uvicorn.run(
        app,
        host=settings.host,
        port=settings.port,
        reload=settings.debug,
        log_config=None
    )