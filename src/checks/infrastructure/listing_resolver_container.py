"""Контейнер для use-case резолвинга листингов."""

from __future__ import annotations

import httpx

from sources.application.use_cases import ResolveListingFromUrlUseCase
from sources.infrastructure.avito import AvitoListingProvider

_use_case: ResolveListingFromUrlUseCase | None = None


def _client_factory() -> httpx.Client:
    """Создать httpx client для провайдера."""

    return httpx.Client(
        timeout=10.0,
        follow_redirects=True,
        headers={
            'User-Agent': 'flaffy/listing-resolver',
        },
    )


def get_listing_resolver_use_case() -> ResolveListingFromUrlUseCase:
    """Вернуть singleton use-case для резолвинга листингов."""

    global _use_case
    if _use_case is not None:
        return _use_case

    provider = AvitoListingProvider(client_factory=_client_factory)
    _use_case = ResolveListingFromUrlUseCase((provider,))
    return _use_case


def close_listing_resolver_container() -> None:
    """Сбросить use-case (клиенты создаются по запросу)."""

    global _use_case
    _use_case = None
