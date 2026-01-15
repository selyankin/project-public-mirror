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
    DATABASE_URL: str | None = None
    DB_DSN: str | None = None
    DB_ECHO: bool = False
    DB_POOL_SIZE: int = 5
    DB_MAX_OVERFLOW: int = 10
    LOG_LEVEL: LogLevel = 'INFO'
    SERVICE_NAME: str = 'flaffy'
    DEBUG: bool = False
    APP_TIMEZONE: str = 'Europe/Stockholm'
    FIAS_MODE: Literal['stub', 'api'] = 'stub'
    FIAS_BASE_URL: str | None = None
    FIAS_TOKEN: str | None = None
    FIAS_TIMEOUT_SECONDS: float = 10.0
    FIAS_RETRIES: int = 2
    FIAS_RETRY_BACKOFF_SECONDS: float = 0.5
    FIAS_CONCURRENCY_LIMIT: int = 5
    FIAS_SUGGEST_ENDPOINT: str = '/api/spas/v2.0/SearchAddressItem'
    ROSREESTR_MODE: Literal['stub', 'api_cloud'] = 'stub'
    ROSREESTR_TOKEN: str | None = None
    ROSREESTR_TIMEOUT_SECONDS: int = 120
    ROSREESTR_CACHE_MODE: Literal['none', 'memory'] = 'memory'
    ROSREESTR_CACHE_TTL_SECONDS: int = 86400
    GIS_GKH_MODE: Literal['stub', 'playwright'] = 'stub'
    GIS_GKH_TIMEOUT_SECONDS: int = 60
    GIS_GKH_HEADLESS: bool = True
    GIS_GKH_SSL_VERIFY: bool = True
    KAD_ARBITR_MODE: str = 'stub'
    KAD_ARBITR_BASE_URL: str = 'https://kad.arbitr.ru'
    KAD_ARBITR_TIMEOUT_SECONDS: int = 30
    KAD_ARBITR_SSL_VERIFY: bool = True
    KAD_ARBITR_USER_AGENT: str | None = None
    KAD_ARBITR_MAX_PAGES: int = 2
    KAD_ARBITR_MAX_CASES_TO_ENRICH: int = 20
    KAD_ARBITR_MAX_DOCS_TO_PARSE_PER_CASE: int = 1
    KAD_ARBITR_RATE_LIMIT_SECONDS: float = 0.4
    KAD_ARBITR_CACHE_ENABLED: bool = True
    KAD_ARBITR_CACHE_MAX_ITEMS: int = 256
    KAD_ARBITR_CACHE_TTL_SECONDS: int = 900
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
    def validate_db_dsn(cls, value: str | None) -> str | None:
        """Проверить валидность DSN, если он передан."""

        if value is None:
            return None

        if not any(
            value.startswith(scheme) for scheme in cls._database_schemes
        ):
            raise ValueError(
                'DB_DSN must use one of the supported PostgreSQL schemes.',
            )

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

        if self.STORAGE_MODE == 'db' and not self.DB_DSN:
            raise ValueError('DB_DSN is required when STORAGE_MODE=db.')

        return self


@cache
def get_settings() -> Settings:
    """Return a cached Settings instance."""
    return Settings()
