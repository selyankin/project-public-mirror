"""Shared configuration settings for the Flaffy services."""

from functools import cache
from typing import ClassVar, Literal

from pydantic import field_validator, model_validator
from pydantic_settings import BaseSettings, SettingsConfigDict

EnvName = Literal['local', 'dev', 'test', 'staging', 'prod']
LogLevel = Literal['DEBUG', 'INFO', 'WARNING', 'ERROR', 'CRITICAL']
StorageMode = Literal['memory', 'db']


class Settings(BaseSettings):
    """Base application settings loaded from environment variables."""

    model_config = SettingsConfigDict(
        env_prefix='',
        case_sensitive=False,
        extra='ignore',
        env_file='.env',
    )

    _database_schemes: ClassVar[tuple[str, ...]] = (
        'postgresql://',
        'postgresql+psycopg://',
        'postgresql+asyncpg://',
    )

    APP_ENV: EnvName = 'local'
    DATABASE_URL: str = 'postgresql+asyncpg://localhost:5432/flaffy'
    DB_DSN: str = 'postgresql+asyncpg://test:test@localhost:5432/flaffy_test'
    DB_ECHO: bool = False
    DB_POOL_SIZE: int = 5
    DB_MAX_OVERFLOW: int = 10
    LOG_LEVEL: LogLevel = 'INFO'
    SERVICE_NAME: str = 'flaffy'
    DEBUG: bool = False
    TIMEZONE: str = 'Europe/Stockholm'
    FIAS_MODE: Literal['stub', 'api'] = 'stub'
    FIAS_BASE_URL: str | None = None
    FIAS_TOKEN: str | None = None
    FIAS_TIMEOUT_SECONDS: float = 5.0
    CHECK_CACHE_TTL_SECONDS: int = 600
    CHECK_CACHE_VERSION: str = 'v1'
    STORAGE_MODE: StorageMode = 'db'

    @property
    def is_prod(self) -> bool:
        """Return True when the service runs in production."""
        return self.APP_ENV == 'prod'

    @property
    def is_local(self) -> bool:
        """Return True when the service runs in a local environment."""
        return self.APP_ENV == 'local'

    @property
    def fias_enabled(self) -> bool:
        """Return True if FIAS integration should be used."""
        return self.FIAS_MODE == 'api'

    @field_validator('DATABASE_URL')
    @classmethod
    def validate_database_url(cls, value: str) -> str:
        """Ensure the database URL uses a supported PostgreSQL driver."""
        if not value:
            raise ValueError('DATABASE_URL must be provided.')
        if not any(
            value.startswith(scheme) for scheme in cls._database_schemes
        ):
            raise ValueError(
                'DATABASE_URL must use one of: '
                '"postgresql://", "postgresql+psycopg://", '
                '"postgresql+asyncpg://".',
            )
        return value

    @field_validator('DB_DSN')
    @classmethod
    def validate_db_dsn(cls, value: str) -> str:
        """Убедиться, что DSN указан."""

        if not value:
            raise ValueError('DB_DSN must be provided.')

        return value

    @model_validator(mode='after')
    def validate_fias(self) -> 'Settings':
        """Ensure FIAS settings are configured when API mode is enabled."""
        if self.fias_enabled:
            if not self.FIAS_BASE_URL:
                raise ValueError(
                    'FIAS_BASE_URL is required when FIAS_MODE=api.',
                )
            if not self.FIAS_TOKEN:
                raise ValueError(
                    'FIAS_TOKEN is required when FIAS_MODE=api.',
                )

        return self


@cache
def get_settings() -> Settings:
    """Return a cached Settings instance."""
    return Settings()
