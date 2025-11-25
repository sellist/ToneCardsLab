"""Main FastAPI application"""

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from tcl_api.config import settings
from tcl_api.controllers import health_router


def create_app() -> FastAPI:
    app = FastAPI(
        title=settings.app_name,
        version=settings.app_version,
        debug=settings.debug,
        description="ToneCards Lab API for managing musical language flashcards",
        docs_url="/docs",
        redoc_url="/redoc",
        openapi_url="/openapi.json"
    )

    app.add_middleware(
        CORSMiddleware,
        allow_origins=settings.cors_origins,
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )

    app.include_router(health_router, prefix=settings.api_prefix)

    return app


app = create_app()


@app.get("/")
def root():
    return {
        "message": "Welcome to ToneCards Lab API",
        "version": settings.app_version,
        "docs": "/docs"
    }

