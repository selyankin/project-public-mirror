"""In-memory хранилище результатов проверок адресов."""

from __future__ import annotations

from typing import Final
from uuid import UUID, uuid4

from checks.domain.entities.check_result import CheckResultSnapshot


class InMemoryCheckResultsRepo:
    """Простейшее in-memory хранилище результатов проверок."""

    __slots__ = ('_storage',)

    def __init__(self) -> None:
        """Создать пустой репозиторий."""

        self._storage: dict[UUID, CheckResultSnapshot] = {}

    def save(self, result: CheckResultSnapshot) -> UUID:
        """Сохранить результат и вернуть присвоенный идентификатор."""

        check_id = uuid4()
        self._storage[check_id] = result
        return check_id

    def get(self, check_id: UUID) -> CheckResultSnapshot | None:
        """Получить сохранённый результат по идентификатору."""

        return self._storage.get(check_id)

    def all_ids(self) -> Final[tuple[UUID, ...]]:
        """Вернуть список сохранённых идентификаторов (отладка)."""

        return tuple(self._storage.keys())
