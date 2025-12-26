"""Тесты провайдера AvitoListingProvider."""

from datetime import UTC, datetime

import httpx
import pytest

from sources.domain.exceptions import ListingFetchError
from sources.domain.value_objects import ListingUrl
from sources.infrastructure.avito import AvitoListingProvider


def _build_client(html: str, status: int = 200) -> httpx.Client:
    """Собрать httpx.Client с MockTransport."""

    def handler(_: httpx.Request) -> httpx.Response:
        return httpx.Response(
            status_code=status,
            text=html,
        )

    transport = httpx.MockTransport(handler)
    return httpx.Client(transport=transport)


def test_provider_fetch_and_normalize_success(monkeypatch) -> None:
    """Провайдер возвращает нормализованное объявление."""

    html = """
    <script>
    window.__preloadedState__ = {"data":{"item":{"id":"A-1",
    "title":"Квартира 50 м² 10/16 эт.","fullAddress":"Москва",
    "price":{"value":"5 000 000 ₽"},
    "coordinates":{"latitude":55.5,"longitude":37.5}}}};
    </script>
    """
    client = _build_client(html)
    provider = AvitoListingProvider(client=client)
    url = ListingUrl('https://www.avito.ru/item/1')

    snapshot = provider.fetch_snapshot(url)
    assert snapshot.source == 'avito'
    assert snapshot.url == url
    assert isinstance(snapshot.fetched_at, datetime)
    assert snapshot.fetched_at.tzinfo == UTC

    listing = provider.normalize(snapshot)
    assert listing.listing_id.value == 'A-1'
    assert listing.price == 5_000_000


def test_provider_fetch_snapshot_bad_status() -> None:
    """HTTP != 200 вызывает ListingFetchError."""

    client = _build_client('<html></html>', status=500)
    provider = AvitoListingProvider(client=client)
    url = ListingUrl('https://www.avito.ru/item/2')

    with pytest.raises(ListingFetchError):
        provider.fetch_snapshot(url)
