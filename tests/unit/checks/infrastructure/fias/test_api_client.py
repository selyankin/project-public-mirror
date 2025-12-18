import httpx
import pytest

from checks.infrastructure.fias.client import ApiFiasClient


@pytest.mark.asyncio
async def test_api_client_returns_none_on_non_200():
    async def handler(request: httpx.Request) -> httpx.Response:
        return httpx.Response(500, json={'error': 'boom'})

    transport = httpx.MockTransport(handler)
    async with httpx.AsyncClient(transport=transport) as http_client:
        client = ApiFiasClient(
            base_url='https://fias.example',
            token='token',
            http_client=http_client,
            timeout_seconds=0.1,
            retries=0,
            retry_backoff_seconds=0.0,
            concurrency_limit=1,
            endpoint='/search',
        )
        result = await client.normalize_address('test query')
        assert result is None
