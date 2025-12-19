"""Политика доступа к модулям отчёта."""

from __future__ import annotations

import os
from collections.abc import Iterable

from reports.domain.exceptions.report import ReportModulePaymentRequiredError
from reports.domain.modules.catalog import ReportModuleSpec


class ModuleAccessPolicy:
    """Проверяет, разрешён ли доступ к запрошенным модулям."""

    __slots__ = ('_allow_paid',)

    def __init__(self) -> None:
        """Прочитать конфигурацию доступа к платным модулям."""

        self._allow_paid = os.getenv(
            'REPORTS_ALLOW_PAID_MODULES', ''
        ).lower() in {
            '1',
            'true',
            'yes',
        }

    def ensure_access(self, specs: Iterable[ReportModuleSpec]) -> None:
        """Проверить доступность каждого модуля."""

        if self._allow_paid:
            return

        for spec in specs:
            if spec.is_paid:
                raise ReportModulePaymentRequiredError(spec.id)
