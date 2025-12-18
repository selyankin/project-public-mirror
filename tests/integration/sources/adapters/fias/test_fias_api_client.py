"""Интеграционный smoke-тест ApiFiasClient."""

from __future__ import annotations

import os

import httpx
import pytest

from checks.application.ports.fias_client import NormalizedAddress
from checks.infrastructure.fias.client import ApiFiasClient

pytestmark = pytest.mark.integration


@pytest.mark.asyncio
async def test_api_fias_client_smoke() -> None:
    """Проверка, что клиент может выполнить запрос в режиме API."""

    if os.getenv('FIAS_MODE') != 'api':
        pytest.skip('FIAS_MODE is not api')

    base_url = os.getenv('FIAS_BASE_URL')
    token = os.getenv('FIAS_TOKEN')
    if not base_url or not token:
        pytest.skip('FIAS credentials are not configured')

    endpoint = os.getenv(
        'FIAS_SUGGEST_ENDPOINT',
        '/api/spas/v2.0/SearchAddressItem',
    )
    timeout = float(os.getenv('FIAS_TIMEOUT_SECONDS', '10'))
    retries = int(os.getenv('FIAS_RETRIES', '2'))
    backoff = float(os.getenv('FIAS_RETRY_BACKOFF_SECONDS', '0.5'))
    concurrency = int(os.getenv('FIAS_CONCURRENCY_LIMIT', '5'))

    async with httpx.AsyncClient() as http_client:
        client = ApiFiasClient(
            base_url=base_url,
            token=token,
            http_client=http_client,
            timeout_seconds=timeout,
            retries=retries,
            retry_backoff_seconds=backoff,
            concurrency_limit=concurrency,
            endpoint=endpoint,
        )
        result = await client.normalize_address('г. Москва, ул. Тверская, 1')

    assert result is None or isinstance(result, NormalizedAddress)
