"""Проверка XHR клиента kad.arbitr.ru."""

import httpx
import pytest

from sources.kad_arbitr.exceptions import (
    KadArbitrBlockedError,
    KadArbitrUnexpectedResponseError,
)
from sources.kad_arbitr.models import KadArbitrSearchPayload
from sources.kad_arbitr.xhr_client import XhrKadArbitrClient

pytestmark = pytest.mark.asyncio


async def test_search_instances_success_warmup_once() -> None:
    calls = {'get': 0, 'post': 0}

    def handler(request: httpx.Request) -> httpx.Response:
        if request.method == 'GET' and request.url.path == '/':
            calls['get'] += 1
            return httpx.Response(200, text='ok')
        if (
            request.method == 'POST'
            and request.url.path == '/Kad/SearchInstances'
        ):
            calls['post'] += 1
            return httpx.Response(
                200,
                json={
                    'Items': [
                        {
                            'CaseId': '123',
                            'CaseNumber': 'А40-1/2025',
                            'CourtName': 'Арбитражный суд',
                        }
                    ],
                    'Total': 1,
                    'Page': 1,
                    'Pages': 1,
                },
            )
        return httpx.Response(404, text='not found')

    transport = httpx.MockTransport(handler)
    async with httpx.AsyncClient(
        base_url='https://kad.arbitr.ru',
        transport=transport,
    ) as http_client:
        client = XhrKadArbitrClient(client=http_client)
        payload = KadArbitrSearchPayload()

        response1 = await client.search_instances(payload=payload)
        response2 = await client.search_instances(payload=payload)

    assert calls['get'] == 1
    assert calls['post'] == 2
    assert response1.total == 1
    assert response1.items[0].case_id == '123'
    assert response2.items[0].case_number == 'А40-1/2025'


async def test_search_instances_403_raises_blocked() -> None:
    def handler(request: httpx.Request) -> httpx.Response:
        if request.method == 'GET':
            return httpx.Response(200, text='ok')
        return httpx.Response(403, text='blocked')

    transport = httpx.MockTransport(handler)
    async with httpx.AsyncClient(
        base_url='https://kad.arbitr.ru',
        transport=transport,
    ) as http_client:
        client = XhrKadArbitrClient(client=http_client)
        with pytest.raises(KadArbitrBlockedError):
            await client.search_instances(payload=KadArbitrSearchPayload())


async def test_search_instances_html_raises_unexpected_response() -> None:
    def handler(request: httpx.Request) -> httpx.Response:
        if request.method == 'GET':
            return httpx.Response(200, text='ok')
        return httpx.Response(200, text='<html>blocked</html>')

    transport = httpx.MockTransport(handler)
    async with httpx.AsyncClient(
        base_url='https://kad.arbitr.ru',
        transport=transport,
    ) as http_client:
        client = XhrKadArbitrClient(client=http_client)
        with pytest.raises(KadArbitrUnexpectedResponseError) as exc:
            await client.search_instances(payload=KadArbitrSearchPayload())

    assert 'snippet=' in str(exc.value)
