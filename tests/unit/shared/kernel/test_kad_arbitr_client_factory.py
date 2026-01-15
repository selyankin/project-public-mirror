"""Проверка фабрики клиентов kad.arbitr.ru."""

from types import SimpleNamespace

import pytest

from shared.kernel.kad_arbitr_client_factory import build_kad_arbitr_client
from sources.kad_arbitr.stub_client import StubKadArbitrClient


def test_build_stub_client_by_default() -> None:
    settings = SimpleNamespace(
        KAD_ARBITR_MODE='stub',
        KAD_ARBITR_BASE_URL='https://kad.arbitr.ru',
        KAD_ARBITR_TIMEOUT_SECONDS=30,
        KAD_ARBITR_SSL_VERIFY=True,
        KAD_ARBITR_USER_AGENT=None,
        KAD_ARBITR_RATE_LIMIT_SECONDS=0.0,
        KAD_ARBITR_CACHE_ENABLED=False,
        KAD_ARBITR_CACHE_MAX_ITEMS=16,
        KAD_ARBITR_CACHE_TTL_SECONDS=60,
    )
    client = build_kad_arbitr_client(settings=settings)
    assert isinstance(client, StubKadArbitrClient)


def test_build_xhr_client() -> None:
    settings = SimpleNamespace(
        KAD_ARBITR_MODE='xhr',
        KAD_ARBITR_BASE_URL='https://example.com',
        KAD_ARBITR_TIMEOUT_SECONDS=15,
        KAD_ARBITR_SSL_VERIFY=False,
        KAD_ARBITR_USER_AGENT='ua',
        KAD_ARBITR_RATE_LIMIT_SECONDS=0.1,
        KAD_ARBITR_CACHE_ENABLED=True,
        KAD_ARBITR_CACHE_MAX_ITEMS=16,
        KAD_ARBITR_CACHE_TTL_SECONDS=60,
    )
    client = build_kad_arbitr_client(settings=settings)
    assert client.__class__.__name__ == 'XhrKadArbitrClient'
    assert client.base_url == 'https://example.com'
    assert client.timeout_seconds == 15
    assert client.ssl_verify is False
    assert client.user_agent == 'ua'
    assert client.cache is not None
    assert client.rate_limiter is not None


def test_build_xhr_client_without_cache() -> None:
    settings = SimpleNamespace(
        KAD_ARBITR_MODE='xhr',
        KAD_ARBITR_BASE_URL='https://example.com',
        KAD_ARBITR_TIMEOUT_SECONDS=15,
        KAD_ARBITR_SSL_VERIFY=False,
        KAD_ARBITR_USER_AGENT='ua',
        KAD_ARBITR_RATE_LIMIT_SECONDS=0.0,
        KAD_ARBITR_CACHE_ENABLED=False,
        KAD_ARBITR_CACHE_MAX_ITEMS=16,
        KAD_ARBITR_CACHE_TTL_SECONDS=60,
    )
    client = build_kad_arbitr_client(settings=settings)
    assert client.__class__.__name__ == 'XhrKadArbitrClient'
    assert client.cache is None


def test_build_unknown_mode_raises_value_error() -> None:
    settings = SimpleNamespace(
        KAD_ARBITR_MODE='nope',
        KAD_ARBITR_BASE_URL='https://kad.arbitr.ru',
        KAD_ARBITR_TIMEOUT_SECONDS=30,
        KAD_ARBITR_SSL_VERIFY=True,
        KAD_ARBITR_USER_AGENT=None,
        KAD_ARBITR_RATE_LIMIT_SECONDS=0.0,
        KAD_ARBITR_CACHE_ENABLED=False,
        KAD_ARBITR_CACHE_MAX_ITEMS=16,
        KAD_ARBITR_CACHE_TTL_SECONDS=60,
    )
    with pytest.raises(ValueError):
        build_kad_arbitr_client(settings=settings)
