"""Провайдер объявлений Avito."""

from __future__ import annotations

from datetime import UTC, datetime

import httpx
import orjson

from sources.application.ports import ListingProviderPort
from sources.domain.entities import ListingNormalized, ListingSnapshotRaw
from sources.domain.exceptions import (
    ListingFetchError,
    ListingNotSupportedError,
    ListingParseError,
)
from sources.domain.value_objects import ListingUrl
from sources.infrastructure.avito import (
    extract_preloaded_state_json,
    parse_avito_listing,
)


class AvitoListingProvider(ListingProviderPort):
    """HTTP-провайдер объявлений Avito."""

    __slots__ = ('_client', '_timeout')

    def __init__(
        self,
        *,
        client: httpx.Client | None = None,
        timeout_seconds: float = 10.0,
    ) -> None:
        """Сохранить httpx клиент и таймаут."""

        self._timeout = timeout_seconds
        self._client = client or httpx.Client(timeout=timeout_seconds)

    def is_supported(self, url: ListingUrl) -> bool:
        """Поддерживаются только avito.ru."""

        host = httpx.URL(url.value).host or ''
        return host.endswith('avito.ru')

    def fetch_snapshot(self, url: ListingUrl) -> ListingSnapshotRaw:
        """Загрузить HTML объявления."""

        if not self.is_supported(url):
            raise ListingNotSupportedError('URL не принадлежит avito.ru')

        try:
            response = self._client.get(
                url.value,
                timeout=self._timeout,
            )
        except (httpx.TimeoutException, httpx.RequestError) as exc:
            raise ListingFetchError(str(exc)) from exc

        if response.status_code != 200:
            raise ListingFetchError(
                f'HTTP {response.status_code} при загрузке объявления',
            )

        return ListingSnapshotRaw(
            source='avito',
            url=url,
            fetched_at=datetime.now(UTC),
            raw_html=response.text,
        )

    def normalize(self, snapshot: ListingSnapshotRaw) -> ListingNormalized:
        """Преобразовать HTML в ListingNormalized."""

        json_str = extract_preloaded_state_json(snapshot.raw_html)
        try:
            data = orjson.loads(json_str)
        except orjson.JSONDecodeError as exc:
            raise ListingParseError('preloaded state corrupted') from exc

        if not isinstance(data, dict):
            raise ListingParseError('preloaded state не содержит объект')

        return parse_avito_listing(
            url=snapshot.url,
            preloaded_state=data,
        )
