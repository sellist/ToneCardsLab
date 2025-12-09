from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from tcl_api.config import settings, setup_logging, get_logger
from tcl_api.controllers import health_router, note_router
from tcl_api.middleware import LoggingMiddleware
from tcl_api.exceptions import setup_exception_handlers
from tcl_api.internal.musicache import build_music_cache, set_cache
from contextlib import asynccontextmanager

setup_logging()
logger = get_logger("main")


def create_app() -> FastAPI:
    logger.info("Creating FastAPI application")

    @asynccontextmanager
    async def lifespan(app: FastAPI):
        logger.info(f"Starting {settings.app_name} v{settings.app_version}")
        logger.info(f"Debug mode: {settings.debug}")
        logger.info(f"API prefix: {settings.api_prefix}")
        logger.info(f"CORS origins: {settings.cors_origins}")

        music_cache = build_music_cache()
        set_cache(music_cache)
        logger.info("Music cache initialized")

        yield

        logger.info(f"Shutting down {settings.app_name}")

    app = FastAPI(
        title=settings.app_name,
        version=settings.app_version,
        debug=settings.debug,
        description="ToneCards Lab API for managing musical language flashcards",
        docs_url="/docs",
        redoc_url="/redoc",
        openapi_url="/openapi.json",
        lifespan=lifespan
    )

    app.add_middleware(LoggingMiddleware)

    logger.info("Adding CORS middleware")
    app.add_middleware(
        CORSMiddleware,
        allow_origins=settings.cors_origins,
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )

    logger.info("Loading routers")
    app.include_router(health_router, prefix=settings.api_prefix)
    app.include_router(note_router, prefix=settings.api_prefix)

    logger.info("Setting up exception handlers")
    setup_exception_handlers(app)

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
