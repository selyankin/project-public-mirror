"""Тесты получения HTML актов дела kad.arbitr.ru."""

import httpx
import pytest

from sources.kad_arbitr.xhr_client import XhrKadArbitrClient

pytestmark = pytest.mark.asyncio


async def test_get_case_acts_html_warmup_once() -> None:
    calls: dict[str, int] = {'/': 0, '/Card/123': 0}

    def handler(request: httpx.Request) -> httpx.Response:
        calls[request.url.path] = calls.get(request.url.path, 0) + 1
        if request.url.path == '/':
            return httpx.Response(200, text='ok')
        if request.url.path == '/Card/123':
            body = '<html>' + ('x' * 220) + '</html>'
            return httpx.Response(200, text=body)
        return httpx.Response(404, text='not found')

    transport = httpx.MockTransport(handler)
    async_client = httpx.AsyncClient(
        base_url='https://kad.arbitr.ru',
        transport=transport,
    )
    client = XhrKadArbitrClient(client=async_client)

    html_first = await client.get_case_acts_html(case_id='123')
    html_second = await client.get_case_acts_html(case_id='123')

    assert html_first == html_second
    assert calls['/'] == 1
    assert calls['/Card/123'] == 2

    await async_client.aclose()
