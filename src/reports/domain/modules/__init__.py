"""Пакет модулей отчёта."""

from reports.domain.modules.catalog import (
    DEFAULT_MODULE_SPECS,
    DEFAULT_MODULES,
    MODULE_CATALOG,
    ReportModuleSpec,
)
from reports.domain.modules.validation import validate_modules

__all__ = [
    'DEFAULT_MODULES',
    'DEFAULT_MODULE_SPECS',
    'MODULE_CATALOG',
    'ReportModuleSpec',
    'validate_modules',
]
