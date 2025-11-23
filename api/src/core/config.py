from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    """Application settings."""

    app_name: str = "ToneCards API"
    app_version: str = "1.0.0"
    api_prefix: str = "/v1"


settings = Settings()

