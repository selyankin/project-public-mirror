"""Фабрика клиентов ФИАС."""

from __future__ import annotations

import httpx

from checks.application.ports.fias_client import FiasClient
from checks.infrastructure.fias.client import ApiFiasClient
from checks.infrastructure.fias.client_stub import StubFiasClient
from shared.kernel.settings import Settings


def get_fias_client(
    settings: Settings,
    http_client: httpx.AsyncClient | None,
) -> FiasClient:
    """Вернуть клиента ФИАС, соответствующего режиму настроек."""

    if settings.FIAS_MODE == 'stub':
        return StubFiasClient()

    if http_client is None:
        raise RuntimeError('HTTP client is required for FIAS API mode.')

    if not settings.FIAS_BASE_URL or not settings.FIAS_TOKEN:
        raise RuntimeError('FIAS_BASE_URL and FIAS_TOKEN must be configured.')

    return ApiFiasClient(
        base_url=settings.FIAS_BASE_URL,
        token=settings.FIAS_TOKEN,
        http_client=http_client,
        timeout_seconds=settings.FIAS_TIMEOUT_SECONDS,
        retries=settings.FIAS_RETRIES,
        retry_backoff_seconds=settings.FIAS_RETRY_BACKOFF_SECONDS,
        concurrency_limit=settings.FIAS_CONCURRENCY_LIMIT,
        endpoint=settings.FIAS_SUGGEST_ENDPOINT,
    )
