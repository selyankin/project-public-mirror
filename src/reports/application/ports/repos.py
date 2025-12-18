"""Порты репозиториев отчётов."""

from __future__ import annotations

from typing import Protocol
from uuid import UUID

from reports.domain.entities.report import Report


class ReportsRepoPort(Protocol):
    """Репозиторий доменных отчётов."""

    async def save(self, report: Report) -> UUID:
        """Сохранить отчёт."""

    async def get(self, report_id: UUID) -> Report | None:
        """Вернуть отчёт или None."""
