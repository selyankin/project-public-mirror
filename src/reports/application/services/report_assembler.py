"""Сборка отчёта из модулей."""

from __future__ import annotations

from collections.abc import Mapping
from datetime import UTC, datetime
from typing import Any

from reports.application.services.module_builders import ModuleBuilder
from reports.domain.constants import REPORT_SCHEMA_VERSION


class ReportAssembler:
    """Собирает полезную нагрузку отчёта по списку модулей."""

    __slots__ = ('_builders', '_schema_version')

    def __init__(
        self,
        builders: Mapping[str, ModuleBuilder],
        *,
        schema_version: int = REPORT_SCHEMA_VERSION,
    ) -> None:
        """Сохранить доступные сборщики и версию схемы."""

        self._builders = dict(builders)
        self._schema_version = schema_version

    async def assemble(
        self,
        check_payload: dict[str, Any],
        modules: list[str],
    ) -> dict[str, Any]:
        """Сформировать полезную нагрузку отчёта."""

        sections: dict[str, Any] = {}
        for module_id in modules:
            builder = self._builders.get(module_id)
            if builder is None:
                continue

            sections[module_id] = await builder(check_payload)

        meta = {
            'check_id': check_payload['check_id'],
            'generated_at': datetime.now(UTC),
            'schema_version': self._schema_version,
            'modules': list(modules),
        }

        return {
            'meta': meta,
            'sections': sections,
        }
