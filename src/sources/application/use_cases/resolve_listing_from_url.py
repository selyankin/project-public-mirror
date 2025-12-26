"""Use-case получения нормализованного листинга по URL."""

from __future__ import annotations

from collections.abc import Sequence

from sources.application.ports import ListingProviderPort
from sources.domain.entities import ListingNormalized
from sources.domain.exceptions import ListingNotSupportedError
from sources.domain.value_objects import ListingUrl


class ResolveListingFromUrlUseCase:
    """Выбирает подходящего провайдера и нормализует листинг."""

    __slots__ = ('_providers',)

    def __init__(
        self,
        providers: Sequence[ListingProviderPort],
    ) -> None:
        """Сохранить доступных провайдеров."""

        self._providers = tuple(providers)

    def execute(self, url_text: str) -> ListingNormalized:
        """Вернуть нормализованный листинг для URL."""

        url = ListingUrl(url_text)
        provider = self._resolve_provider(url)
        snapshot = provider.fetch_snapshot(url)
        return provider.normalize(snapshot)

    def _resolve_provider(self, url: ListingUrl) -> ListingProviderPort:
        """Найти провайдера, который поддерживает URL."""

        for provider in self._providers:
            if provider.is_supported(url):
                return provider

        raise ListingNotSupportedError('no provider for URL')
