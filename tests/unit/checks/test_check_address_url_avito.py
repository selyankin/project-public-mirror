"""Интеграция CheckAddressUseCase с listing resolver."""

from __future__ import annotations

import pytest

from checks.application.use_cases.address_risk_check import (
    AddressRiskCheckResult,
)
from checks.application.use_cases.check_address import CheckAddressUseCase
from checks.domain.value_objects.address import (
    normalize_address,
    normalize_address_raw,
)
from checks.domain.value_objects.query import CheckQuery
from checks.infrastructure.check_cache_repo_inmemory import (
    InMemoryCheckCacheRepo,
)
from checks.infrastructure.check_results_repo_inmemory import (
    InMemoryCheckResultsRepo,
)
from checks.infrastructure.fias.client_stub import StubFiasClient
from risks.application.scoring import build_risk_card
from sources.domain.entities import ListingNormalized
from sources.domain.exceptions import ListingFetchError
from sources.domain.value_objects import ListingId, ListingUrl

pytestmark = pytest.mark.asyncio


class ListingResolverStub:
    """Возврат фиктивного листинга."""

    def __init__(self, listing: ListingNormalized | None) -> None:
        self.listing = listing
        self.calls = 0

    def execute(self, url_text: str) -> ListingNormalized:
        self.calls += 1
        if self.listing is None:
            raise RuntimeError('no listing configured')
        return self.listing


class FakeAddressRiskCheckUseCase:
    """Считает вызовы и возвращает фиктивный результат."""

    def __init__(self, normalized_text: str) -> None:
        normalized = normalize_address(normalize_address_raw(normalized_text))
        self._result = AddressRiskCheckResult(
            normalized_address=normalized,
            signals=[],
            risk_card=build_risk_card(()),
        )
        self.called_with = None

    async def execute(self, raw):
        self.called_with = raw
        return self._result


async def test_url_without_address_uses_listing(monkeypatch) -> None:
    """Когда URL без query, используем листинг Avito."""

    listing = ListingNormalized(
        source='avito',
        url=ListingUrl('https://www.avito.ru/item/1'),
        listing_id=ListingId('listing-1'),
        address_text='г. Москва, ул. Тверская, 1',
    )
    listing_resolver = ListingResolverStub(listing)
    monkeypatch.setattr(
        'checks.application.use_cases.check_address.'
        'get_listing_resolver_use_case',
        lambda: listing_resolver,
    )
    fake_risk = FakeAddressRiskCheckUseCase(listing.address_text)
    use_case = CheckAddressUseCase(
        address_risk_check_use_case=fake_risk,
        check_results_repo=InMemoryCheckResultsRepo(),
        check_cache_repo=InMemoryCheckCacheRepo(ttl_seconds=600),
        fias_client=StubFiasClient(),
        fias_mode='stub',
        cache_version='test',
    )

    query = CheckQuery({'type': 'url', 'query': listing.url.value})
    result = await use_case.execute_query(query)

    assert fake_risk.called_with is not None
    assert result['check_id'] is not None
    assert listing_resolver.calls == 1
    assert result['listing']['listing_id'] == 'listing-1'
    assert result['listing']['coords']['lat'] is None
    assert all(
        sig['code'] != 'url_not_supported_yet' for sig in result['signals']
    )


async def test_listing_error_added_on_fetch_failure(monkeypatch) -> None:
    """Если провайдер падает, в ответе появляется listing_error."""

    class ErrorResolver:
        def execute(self, url_text: str):
            raise ListingFetchError('boom')

    resolver = ErrorResolver()
    monkeypatch.setattr(
        'checks.application.use_cases.check_address.'
        'get_listing_resolver_use_case',
        lambda: resolver,
    )
    use_case = CheckAddressUseCase(
        address_risk_check_use_case=FakeAddressRiskCheckUseCase(
            'г. Москва',
        ),
        check_results_repo=InMemoryCheckResultsRepo(),
        check_cache_repo=InMemoryCheckCacheRepo(ttl_seconds=600),
        fias_client=StubFiasClient(),
        fias_mode='stub',
        cache_version='test',
    )

    query = CheckQuery({'type': 'url', 'query': 'https://avito.ru/item/err'})
    result = await use_case.execute_query(query)

    assert result['listing_error'] == 'ListingFetchError'
    assert any(
        sig['code'] == 'url_not_supported_yet' for sig in result['signals']
    )
