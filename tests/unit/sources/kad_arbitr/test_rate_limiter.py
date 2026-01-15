"""Проверка ограничителя частоты запросов."""

import pytest

from sources.kad_arbitr.throttling import RateLimiter

pytestmark = pytest.mark.asyncio


async def test_rate_limiter_zero_interval_no_sleep() -> None:
    calls: list[float] = []

    async def _sleep(value: float) -> None:
        calls.append(value)

    limiter = RateLimiter(
        min_interval_seconds=0.0,
        sleep_fn=_sleep,
    )

    await limiter.wait()
    await limiter.wait()

    assert calls == []


async def test_rate_limiter_waits_when_needed() -> None:
    calls: list[float] = []
    times = iter([0.0, 0.1, 1.0])

    async def _sleep(value: float) -> None:
        calls.append(value)

    limiter = RateLimiter(
        min_interval_seconds=1.0,
        now_fn=lambda: next(times),
        sleep_fn=_sleep,
    )

    await limiter.wait()
    await limiter.wait()

    assert calls == [0.9]
