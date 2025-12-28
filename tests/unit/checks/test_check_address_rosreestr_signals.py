"""Проверка сигналов Росреестра в payload проверки."""

from datetime import UTC, datetime
from types import SimpleNamespace

import pytest

from checks.adapters.address_resolver_stub import AddressResolverStub
from checks.adapters.signals_provider_stub import SignalsProviderStub
from checks.application.ports.fias_client import NormalizedAddress
from checks.application.use_cases.address_risk_check import (
    AddressRiskCheckUseCase,
)
from checks.application.use_cases.check_address import CheckAddressUseCase
from checks.domain.value_objects.query import CheckQuery
from checks.infrastructure.check_cache_repo_inmemory import (
    InMemoryCheckCacheRepo,
)
from checks.infrastructure.check_results_repo_inmemory import (
    InMemoryCheckResultsRepo,
)
from sources.domain.entities import ListingNormalized
from sources.domain.value_objects import ListingId, ListingUrl
from sources.rosreestr.models import RosreestrHouseNormalized

pytestmark = pytest.mark.asyncio


class _ListingResolverStub:
    def __init__(self, listing: ListingNormalized):
        self.listing = listing
        self.calls: list[str] = []

    def execute(self, url_text: str):
        self.calls.append(url_text)
        return self.listing


class _FiasClientStub:
    async def normalize_address(self, query: str) -> NormalizedAddress | None:
        return NormalizedAddress(
            source_query=query,
            normalized='г. Москва, ул. Тверская, д. 1',
            fias_id='fias-main',
            confidence=0.95,
            raw={'query': query},
            cadastral_number='77:01:000101:1',
            updated_at=datetime(2024, 5, 1, tzinfo=UTC),
        )


class _RosreestrResolverStub:
    def __init__(self, result):
        self._result = result

    def execute(self, *, cadastral_number: str):
        return self._result


def _make_listing(area_total: float) -> ListingNormalized:
    return ListingNormalized(
        source='avito',
        url=ListingUrl('https://avito.ru/item'),
        listing_id=ListingId('listing-1'),
        title='Лот',
        address_text='г. Москва, ул. Тверская, д. 1',
        area_total=area_total,
    )


def _build_use_case(monkeypatch, listing, rosreestr_result):
    listing_stub = _ListingResolverStub(listing)
    rosreestr_stub = _RosreestrResolverStub(rosreestr_result)
    monkeypatch.setattr(
        'checks.application.use_cases.check_address.'
        'get_listing_resolver_use_case',
        lambda: listing_stub,
    )
    monkeypatch.setattr(
        'checks.application.use_cases.check_address.'
        'get_rosreestr_resolver_use_case',
        lambda settings: rosreestr_stub,
    )
    address_resolver = AddressResolverStub({})
    signals_provider = SignalsProviderStub({})
    address_risk_use_case = AddressRiskCheckUseCase(
        address_resolver=address_resolver,
        signals_provider=signals_provider,
    )
    use_case = CheckAddressUseCase(
        address_risk_check_use_case=address_risk_use_case,
        check_results_repo=InMemoryCheckResultsRepo(),
        check_cache_repo=InMemoryCheckCacheRepo(ttl_seconds=600),
        fias_client=_FiasClientStub(),
        fias_mode='stub',
        cache_version='test',
        settings=SimpleNamespace(ROSREESTR_MODE='stub'),
    )
    return use_case


async def test_rosreestr_area_mismatch_signal(monkeypatch):
    listing = _make_listing(area_total=120.0)
    rosreestr_house = RosreestrHouseNormalized(area_total=80.0)
    use_case = _build_use_case(monkeypatch, listing, rosreestr_house)

    query = CheckQuery({'type': 'url', 'query': 'https://avito.ru/item'})
    result = await use_case.execute_query(query)

    signals = result['sources']['rosreestr']['signals']
    codes = {signal['code'] for signal in signals}
    assert 'area_mismatch' in codes


async def test_rosreestr_area_match_signal(monkeypatch):
    listing = _make_listing(area_total=105.0)
    rosreestr_house = RosreestrHouseNormalized(area_total=100.0)
    use_case = _build_use_case(monkeypatch, listing, rosreestr_house)

    query = CheckQuery({'type': 'url', 'query': 'https://avito.ru/item'})
    result = await use_case.execute_query(query)

    signals = result['sources']['rosreestr']['signals']
    codes = {signal['code'] for signal in signals}
    assert 'area_match' in codes
