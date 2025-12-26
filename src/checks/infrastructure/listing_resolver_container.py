"""Контейнер для use-case резолвинга листингов."""

from __future__ import annotations

import httpx

from sources.application.use_cases import ResolveListingFromUrlUseCase
from sources.infrastructure.avito import AvitoListingProvider

_client: httpx.Client | None = None
_use_case: ResolveListingFromUrlUseCase | None = None


def get_listing_resolver_use_case() -> ResolveListingFromUrlUseCase:
    """Вернуть singleton use-case для резолвинга листингов."""

    global _client, _use_case
    if _use_case is not None:
        return _use_case

    _client = httpx.Client(timeout=10.0)
    provider = AvitoListingProvider(client=_client)
    _use_case = ResolveListingFromUrlUseCase((provider,))
    return _use_case


def close_listing_resolver_container() -> None:
    """Закрыть ресурсы контейнера."""

    global _client, _use_case
    if _client is not None:
        _client.close()
    _client = None
    _use_case = None
