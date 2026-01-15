"""LRU TTL кэш для kad.arbitr.ru."""

from __future__ import annotations

import time
from collections import OrderedDict
from collections.abc import Callable
from dataclasses import dataclass
from typing import Any


@dataclass(slots=True)
class CacheItem:
    """Элемент кэша."""

    value: Any
    expires_at: float


class LruTtlCache:
    """LRU кэш с TTL."""

    def __init__(
        self,
        *,
        max_items: int,
        ttl_seconds: int,
        now_fn: Callable[[], float] | None = None,
    ) -> None:
        """Сконфигурировать кэш."""

        self._max_items = max_items
        self._ttl_seconds = ttl_seconds
        self._now = now_fn or time.monotonic
        self._items: OrderedDict[object, CacheItem] = OrderedDict()

    def get(self, key: object) -> Any | None:
        """Получить значение из кэша."""

        item = self._items.get(key)
        if item is None:
            return None

        if item.expires_at <= self._now():
            self._items.pop(key, None)
            return None

        self._items.move_to_end(key)
        return item.value

    def set(self, key: object, value: Any) -> None:
        """Сохранить значение в кэш."""

        expires_at = self._now() + self._ttl_seconds
        self._items[key] = CacheItem(value=value, expires_at=expires_at)
        self._items.move_to_end(key)
        self._purge()

    def _purge(self) -> None:
        """Очистить кэш от протухших и лишних элементов."""

        now = self._now()
        expired = [
            key for key, item in self._items.items() if item.expires_at <= now
        ]
        for key in expired:
            self._items.pop(key, None)

        while len(self._items) > self._max_items:
            self._items.popitem(last=False)
