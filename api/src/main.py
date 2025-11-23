from fastapi import FastAPI
from src.core.config import settings
from src.controllers import health_controller, hello_controller

app = FastAPI(
    title=settings.app_name,
    version=settings.app_version,
    description="A basic ToneCards API with health check and hello endpoints",
)

app.include_router(
    health_controller.router,
    prefix=settings.api_prefix,
)
app.include_router(
    hello_controller.router,
    prefix=settings.api_prefix,
)


@app.get("/")
def root():
    return {
        "message": f"Welcome to {settings.app_name}",
        "version": settings.app_version,
        "docs": "/docs",
    }


if __name__ == "__main__":
    import uvicorn

    uvicorn.run(
        "main:app",
        host="0.0.0.0",
        port=8000,
        reload=True,
    )

