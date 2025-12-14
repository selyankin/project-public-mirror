"""Shared configuration settings for the Mirano services."""

from functools import cache
from typing import ClassVar, Literal

from pydantic import field_validator
from pydantic_settings import BaseSettings, SettingsConfigDict

EnvName = Literal["local", "dev", "test", "staging", "prod"]
LogLevel = Literal["DEBUG", "INFO", "WARNING", "ERROR", "CRITICAL"]


class Settings(BaseSettings):
    """Base application settings loaded from environment variables."""

    model_config = SettingsConfigDict(
        env_prefix="",
        case_sensitive=False,
        extra="ignore",
        env_file=".env",
    )

    _database_schemes: ClassVar[tuple[str, ...]] = (
        "postgresql://",
        "postgresql+psycopg://",
        "postgresql+asyncpg://",
    )

    APP_ENV: EnvName = "local"
    DATABASE_URL: str
    LOG_LEVEL: LogLevel = "INFO"
    SERVICE_NAME: str = "mirano"
    DEBUG: bool = False
    TIMEZONE: str = "Europe/Stockholm"

    @property
    def is_prod(self) -> bool:
        """Return True when the service runs in production."""
        return self.APP_ENV == "prod"

    @property
    def is_local(self) -> bool:
        """Return True when the service runs in a local environment."""
        return self.APP_ENV == "local"

    @field_validator("DATABASE_URL")
    @classmethod
    def validate_database_url(cls, value: str) -> str:
        """Ensure the database URL uses a supported PostgreSQL driver."""
        if not value:
            raise ValueError("DATABASE_URL must be provided.")
        if not any(
            value.startswith(scheme) for scheme in cls._database_schemes
        ):
            raise ValueError(
                "DATABASE_URL must use one of: "
                '"postgresql://", "postgresql+psycopg://", '
                '"postgresql+asyncpg://".',
            )
        return value


@cache
def get_settings() -> Settings:
    """Return a cached Settings instance."""
    return Settings()
