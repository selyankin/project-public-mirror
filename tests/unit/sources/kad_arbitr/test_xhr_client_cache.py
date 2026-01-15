"""Проверка кэширования в XhrKadArbitrClient."""

import httpx
import pytest

from sources.kad_arbitr.cache import LruTtlCache
from sources.kad_arbitr.models import KadArbitrSearchPayload
from sources.kad_arbitr.throttling import RateLimiter
from sources.kad_arbitr.xhr_client import XhrKadArbitrClient

pytestmark = pytest.mark.asyncio


async def test_xhr_client_uses_cache_for_card_and_search() -> None:
    calls = {'/': 0, '/Card/123': 0, '/Kad/SearchInstances': 0}

    def handler(request: httpx.Request) -> httpx.Response:
        calls[request.url.path] = calls.get(request.url.path, 0) + 1
        if request.url.path == '/':
            return httpx.Response(200, text='ok')
        if request.url.path == '/Card/123':
            body = '<html>' + ('x' * 220) + '</html>'
            return httpx.Response(200, text=body)
        if request.url.path == '/Kad/SearchInstances':
            return httpx.Response(
                200,
                json={
                    'Items': [
                        {
                            'CaseId': '1',
                            'CaseNumber': 'А40-1/2025',
                        }
                    ],
                    'Total': 1,
                    'Page': 1,
                    'Pages': 1,
                },
            )
        return httpx.Response(404, text='not found')

    transport = httpx.MockTransport(handler)
    async_client = httpx.AsyncClient(
        base_url='https://kad.arbitr.ru',
        transport=transport,
    )
    cache = LruTtlCache(max_items=10, ttl_seconds=60)
    limiter = RateLimiter(min_interval_seconds=0.0)
    client = XhrKadArbitrClient(
        client=async_client,
        cache=cache,
        rate_limiter=limiter,
    )

    await client.get_case_card_html(case_id='123')
    await client.get_case_card_html(case_id='123')

    payload = KadArbitrSearchPayload()
    await client.search_instances(payload=payload)
    await client.search_instances(payload=payload)

    assert calls['/'] == 1
    assert calls['/Card/123'] == 1
    assert calls['/Kad/SearchInstances'] == 1

    await async_client.aclose()
