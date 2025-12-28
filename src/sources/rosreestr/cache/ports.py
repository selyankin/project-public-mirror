"""Порты кэша Росреестра."""

from __future__ import annotations

from typing import Protocol


class RosreestrCachePort(Protocol):
    """Кэш Rosreestr API."""

    def get(self, *, key: str) -> dict[str, object] | None:
        """Получить значение по ключу."""

    def set(
        self,
        *,
        key: str,
        value: dict[str, object],
        ttl_seconds: int,
    ) -> None:
        """Сохранить значение с TTL."""
