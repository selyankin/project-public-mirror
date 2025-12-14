"""Shared logging configuration utilities."""

import logging
from logging.config import dictConfig
from typing import Final

from src.shared.kernel.settings import get_settings

_configured: bool = False
_LEVEL_NAMES: Final[dict[str, int]] = logging.getLevelNamesMapping()


def _normalize_level(level_name: str) -> tuple[str, int]:
    """Convert log-level"""

    normalized = level_name.upper()
    value = _LEVEL_NAMES.get(normalized, logging.INFO)
    resolved_name = logging.getLevelName(value)
    return resolved_name, value


def setup_logging() -> None:
    """Configure the root logger for the application."""

    global _configured
    if _configured:
        return

    settings = get_settings()
    root_level_name, root_level_value = _normalize_level(settings.LOG_LEVEL)
    access_level_name = (
        "INFO" if root_level_value < logging.INFO else root_level_name
    )

    dictConfig(
        {
            "version": 1,
            "disable_existing_loggers": False,
            "formatters": {
                "default": {
                    "format": "%(asctime)s | %(levelname)s | %(name)s | "
                    "%(message)s",
                },
            },
            "handlers": {
                "default": {
                    "class": "logging.StreamHandler",
                    "stream": "ext://sys.stdout",
                    "formatter": "default",
                },
            },
            "loggers": {
                "uvicorn": {
                    "handlers": ["default"],
                    "level": root_level_name,
                    "propagate": False,
                },
                "uvicorn.error": {
                    "handlers": ["default"],
                    "level": root_level_name,
                    "propagate": False,
                },
                "uvicorn.access": {
                    "handlers": ["default"],
                    "level": access_level_name,
                    "propagate": False,
                },
            },
            "root": {
                "level": root_level_name,
                "handlers": ["default"],
            },
        },
    )

    _configured = True


def get_logger(name: str | None = None) -> logging.Logger:
    """Return a named logger or the service logger by default."""

    if name:
        return logging.getLogger(name)

    service_name = get_settings().SERVICE_NAME
    return logging.getLogger(service_name)
