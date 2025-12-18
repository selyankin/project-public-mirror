"""In-memory репозиторий отчётов."""

from __future__ import annotations

from typing import Final
from uuid import UUID

from reports.domain.entities.report import Report


class InMemoryReportsRepo:
    """Простейшее хранилище отчётов в памяти."""

    __slots__ = ('_storage',)

    def __init__(self) -> None:
        """Создать пустой репозиторий."""

        self._storage: dict[UUID, Report] = {}

    async def save(self, report: Report) -> UUID:
        """Сохранить отчёт и вернуть его ID."""

        self._storage[report.id] = report
        return report.id

    async def get(self, report_id: UUID) -> Report | None:
        """Получить отчёт по идентификатору."""

        return self._storage.get(report_id)

    def all_ids(self) -> Final[tuple[UUID, ...]]:
        """Отладочный список ID отчётов."""

        return tuple(self._storage.keys())
