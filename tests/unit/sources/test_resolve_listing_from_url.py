"""Проверки use-case резолвинга листинга по URL."""

from __future__ import annotations

from datetime import UTC, datetime

import pytest

from sources.application.ports import ListingProviderPort
from sources.application.use_cases import ResolveListingFromUrlUseCase
from sources.domain.entities import ListingNormalized, ListingSnapshotRaw
from sources.domain.exceptions import ListingNotSupportedError
from sources.domain.value_objects import ListingId, ListingUrl


class _FakeProvider(ListingProviderPort):
    """Простой провайдер для тестов."""

    def __init__(self, expected_host: str) -> None:
        self._expected_host = expected_host

    def is_supported(self, url: ListingUrl) -> bool:
        return self._expected_host in url.value

    def fetch_snapshot(self, url: ListingUrl) -> ListingSnapshotRaw:
        return ListingSnapshotRaw(
            source='fake',
            url=url,
            fetched_at=datetime.now(UTC),
            raw_html='<html></html>',
        )

    def normalize(self, snapshot: ListingSnapshotRaw) -> ListingNormalized:
        return ListingNormalized(
            source='fake',
            url=snapshot.url,
            listing_id=ListingId('fake-1'),
        )


def test_resolve_listing_success() -> None:
    """Use-case выбирает подходящего провайдера."""

    provider = _FakeProvider('example.com')
    use_case = ResolveListingFromUrlUseCase((provider,))

    listing = use_case.execute('https://example.com/listing/1')

    assert listing.listing_id.value == 'fake-1'
    assert listing.source == 'fake'


def test_resolve_listing_no_provider() -> None:
    """Если нет провайдера, поднимается ListingNotSupportedError."""

    use_case = ResolveListingFromUrlUseCase(())

    with pytest.raises(ListingNotSupportedError):
        use_case.execute('https://unsupported.com/item')
