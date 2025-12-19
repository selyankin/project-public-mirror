"""Реестр сборщиков модулей отчёта."""

from __future__ import annotations

from collections.abc import Awaitable, Callable
from typing import Any, Final

from reports.application.services.module_builders import (
    address_quality,
    base_summary,
    fias_normalization,
    risk_signals,
)

ModuleBuilder = Callable[[dict[str, Any]], Awaitable[dict[str, Any]]]

DEFAULT_MODULE_BUILDERS: Final[dict[str, ModuleBuilder]] = {
    'base_summary': base_summary.build,
    'address_quality': address_quality.build,
    'risk_signals': risk_signals.build,
    'fias_normalization': fias_normalization.build,
}
