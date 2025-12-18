"""In-memory кэш результатов проверок."""

from __future__ import annotations

from collections.abc import Callable
from datetime import UTC, datetime, timedelta
from uuid import UUID

from checks.domain.entities.check_cache import CachedCheckEntry


class InMemoryCheckCacheRepo:
    """Хранит ключи проверок и их идентификаторы с TTL."""

    __slots__ = ('_ttl', '_now_fn', '_storage')

    def __init__(
        self,
        ttl_seconds: int,
        *,
        now_fn: Callable[[], datetime] | None = None,
    ) -> None:
        """Настроить кэш на использование указанного TTL."""

        self._ttl = timedelta(seconds=ttl_seconds)
        self._now_fn = now_fn or (lambda: datetime.now(UTC))
        self._storage: dict[str, CachedCheckEntry] = {}

    def get(self, key: str) -> CachedCheckEntry | None:
        """Вернуть запись по ключу, если она не протухла."""

        self.cleanup()
        entry = self._storage.get(key)
        if not entry:
            return None

        if entry.is_expired(self._now_fn()):
            self._storage.pop(key, None)
            return None

        return entry

    def set(self, key: str, check_id: UUID) -> None:
        """Сохранить запись кэша."""

        self.cleanup()
        created = self._now_fn()
        entry = CachedCheckEntry(
            check_id=check_id,
            created_at=created,
            expires_at=created + self._ttl,
        )
        self._storage[key] = entry

    def cleanup(self) -> None:
        """Удалить протухшие записи."""

        now = self._now_fn()
        expired_keys = [
            key for key, entry in self._storage.items() if entry.is_expired(now)
        ]
        for key in expired_keys:
            self._storage.pop(key, None)
