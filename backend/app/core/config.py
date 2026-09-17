"""Environment-driven backend configuration."""

from typing import Literal

from pydantic import field_validator, model_validator
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    """Application configuration loaded from environment variables."""

    model_config = SettingsConfigDict(
        env_file=".env",
        env_ignore_empty=True,
        extra="ignore",
    )

    project_name: str = "Citizen Intelligence Layer API"
    api_v1_prefix: str = "/api/v1"
    debug: bool = True
    environment: Literal["development", "test", "staging", "production"] = "development"
    log_level: str = "INFO"
    trusted_hosts: list[str] = ["localhost", "127.0.0.1", "testserver"]
    cors_allowed_origins: list[str] = []

    database_url: str = (
        "postgresql+asyncpg://postgres:postgres@postgres:5432/citizen_intelligence"
    )
    redis_url: str = "redis://redis:6379/0"
    rabbitmq_url: str = "amqp://guest:guest@rabbitmq:5672//"
    celery_result_backend: str = "redis://redis:6379/1"
    celery_worker_concurrency: int = 2

    storage_endpoint: str = ""
    storage_bucket: str = ""
    storage_access_key: str = ""
    storage_secret_key: str = ""
    openai_api_key: str = ""
    jwt_secret: str = ""

    @field_validator("log_level")
    @classmethod
    def normalize_log_level(cls, value: str) -> str:
        """Normalize log levels so logging configuration is predictable."""
        normalized = value.upper()
        if normalized not in {"DEBUG", "INFO", "WARNING", "ERROR", "CRITICAL"}:
            raise ValueError("LOG_LEVEL must be a standard Python logging level.")
        return normalized

    @model_validator(mode="after")
    def validate_production_configuration(self) -> "Settings":
        """Reject known-unsafe defaults when deploying to production."""
        if self.environment != "production":
            return self

        if self.debug:
            raise ValueError("DEBUG must be false in production.")
        if len(self.jwt_secret) < 32:
            raise ValueError("JWT_SECRET must be at least 32 characters in production.")
        if not self.trusted_hosts or any(
            host in {"localhost", "127.0.0.1", "testserver", "*"}
            for host in self.trusted_hosts
        ):
            raise ValueError("TRUSTED_HOSTS must contain deployed hostnames.")
        return self


settings = Settings()
