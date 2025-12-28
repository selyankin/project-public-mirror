"""Unit-тесты кэшированного клиента Росреестра."""

import time

import pytest

from sources.rosreestr.cache.in_memory import InMemoryTtlRosreestrCache
from sources.rosreestr.cached_client import CachedRosreestrClient
from sources.rosreestr.dto import RosreestrApiResponse
from sources.rosreestr.ports import RosreestrClientPort


class _FakeClient(RosreestrClientPort):
    def __init__(self, response: RosreestrApiResponse):
        self.response = response
        self.calls = 0

    def get_object(self, *, cadastral_number: str) -> RosreestrApiResponse:
        self.calls += 1
        return self.response


@pytest.mark.parametrize('ttl', [60])
def test_cached_client_returns_cached_response(ttl: int):
    response = RosreestrApiResponse(status=200, found=True)
    inner = _FakeClient(response)
    cache = InMemoryTtlRosreestrCache()
    client = CachedRosreestrClient(inner=inner, cache=cache, ttl_seconds=ttl)

    first = client.get_object(cadastral_number='77:01:000101:1')
    second = client.get_object(cadastral_number='77:01:000101:1')

    assert first is not second
    assert inner.calls == 1


def test_cached_client_expires(monkeypatch):
    response = RosreestrApiResponse(status=200, found=True)
    inner = _FakeClient(response)
    monotonic = time.monotonic
    current = monotonic()

    def fake_now() -> float:
        return fake_now.value

    fake_now.value = current
    cache = InMemoryTtlRosreestrCache(now_fn=fake_now)
    client = CachedRosreestrClient(inner=inner, cache=cache, ttl_seconds=1)

    client.get_object(cadastral_number='77:01:000101:1')
    fake_now.value = current + 2
    client.get_object(cadastral_number='77:01:000101:1')

    assert inner.calls == 2
