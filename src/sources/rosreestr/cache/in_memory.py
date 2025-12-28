"""Ин-memory TTL кэш для ответов Росреестра."""

from __future__ import annotations

import time
from collections.abc import Callable

from sources.rosreestr.cache.ports import RosreestrCachePort


class InMemoryTtlRosreestrCache(RosreestrCachePort):
    """Простой TTL кэш на словаре."""

    def __init__(
        self,
        *,
        now_fn: Callable[[], float] | None = None,
    ) -> None:
        """Инициализировать кэш."""

        self._store: dict[str, tuple[float, dict[str, object]]] = {}
        self._now = now_fn or time.monotonic

    def get(self, *, key: str) -> dict[str, object] | None:
        """Получить значение, если TTL не истёк."""

        entry = self._store.get(key)
        if not entry:
            return None
        expires_at, value = entry
        if self._now() >= expires_at:
            self._store.pop(key, None)
            return None
        return value

    def set(
        self,
        *,
        key: str,
        value: dict[str, object],
        ttl_seconds: int,
    ) -> None:
        """Сохранить значение с TTL."""

        expires_at = self._now() + max(ttl_seconds, 0)
        self._store[key] = (expires_at, value)
