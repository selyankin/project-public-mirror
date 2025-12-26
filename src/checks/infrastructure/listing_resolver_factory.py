"""Фабрика use-case для получения листингов по URL."""

from __future__ import annotations

from sources.application.use_cases import ResolveListingFromUrlUseCase
from sources.infrastructure.avito import AvitoListingProvider


def build_listing_resolver_use_case() -> ResolveListingFromUrlUseCase:
    """Создать use-case резолвинга листингов."""

    providers = (AvitoListingProvider(),)
    return ResolveListingFromUrlUseCase(providers)
