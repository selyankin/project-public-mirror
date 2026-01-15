"""Ограничитель частоты запросов kad.arbitr.ru."""

from __future__ import annotations

import asyncio
import time
from collections.abc import Awaitable, Callable


class RateLimiter:
    """Простейший rate limiter с минимальным интервалом."""

    def __init__(
        self,
        *,
        min_interval_seconds: float,
        now_fn: Callable[[], float] | None = None,
        sleep_fn: Callable[[float], Awaitable[None]] | None = None,
    ) -> None:
        """Сконфигурировать ограничитель."""

        self._min_interval_seconds = min_interval_seconds
        self._now = now_fn or time.monotonic
        self._sleep = sleep_fn or asyncio.sleep
        self._last_call: float | None = None

    async def wait(self) -> None:
        """Подождать до следующего разрешённого запроса."""

        if self._min_interval_seconds <= 0:
            return

        now = self._now()
        if self._last_call is None:
            self._last_call = now
            return

        elapsed = now - self._last_call
        remaining = self._min_interval_seconds - elapsed
        if remaining > 0:
            await self._sleep(remaining)
            now = self._now()

        self._last_call = now
