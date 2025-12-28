"""Проверка интеграции Росреестра в payload проверки."""

from datetime import date
from types import SimpleNamespace

import pytest

from checks.adapters.address_resolver_stub import AddressResolverStub
from checks.adapters.signals_provider_stub import SignalsProviderStub
from checks.application.ports.fias_client import NormalizedAddress
from checks.application.use_cases.address_risk_check import (
    AddressRiskCheckUseCase,
)
from checks.application.use_cases.check_address import CheckAddressUseCase
from checks.infrastructure.check_cache_repo_inmemory import (
    InMemoryCheckCacheRepo,
)
from checks.infrastructure.check_results_repo_inmemory import (
    InMemoryCheckResultsRepo,
)
from sources.domain.exceptions import ListingNotSupportedError
from sources.rosreestr.models import RosreestrHouseNormalized

pytestmark = pytest.mark.asyncio


class _ListingResolverStub:
    def execute(self, url_text: str):
        raise ListingNotSupportedError(url_text)


class _FiasClientStub:
    async def normalize_address(self, query: str) -> NormalizedAddress | None:
        return NormalizedAddress(
            source_query=query,
            normalized='г. Москва, ул. Тверская, д. 1',
            fias_id='fias-main',
            confidence=0.95,
            raw={'query': query},
            cadastral_number='77:01:000101:1',
        )


class _RosreestrResolverStub:
    def __init__(self, result):
        self._result = result
        self.calls: list[str] = []

    def execute(self, *, cadastral_number: str):
        self.calls.append(cadastral_number)
        return self._result


@pytest.fixture(autouse=True)
def listing_resolver_stub(monkeypatch):
    stub = _ListingResolverStub()
    monkeypatch.setattr(
        'checks.application.use_cases.check_address.'
        'get_listing_resolver_use_case',
        lambda: stub,
    )
    return stub


def _make_use_case(monkeypatch, rosreestr_stub):
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
    return CheckAddressUseCase(
        address_risk_check_use_case=address_risk_use_case,
        check_results_repo=InMemoryCheckResultsRepo(),
        check_cache_repo=InMemoryCheckCacheRepo(ttl_seconds=600),
        fias_client=_FiasClientStub(),
        fias_mode='stub',
        cache_version='test',
        settings=SimpleNamespace(ROSREESTR_MODE='stub'),
    )


async def test_rosreestr_payload_contains_house(monkeypatch):
    rosreestr_stub = _RosreestrResolverStub(
        RosreestrHouseNormalized(
            cad_number='77:01:000101:1',
            readable_address='г. Москва, ул. Тверская, д. 1',
            area_total=43.9,
            year_build=2010,
            info_update_date=date(2022, 4, 5),
        )
    )
    use_case = _make_use_case(monkeypatch, rosreestr_stub)

    result = await use_case.execute('г. Москва, ул. Тверская, д. 1')

    rosreestr = result['fias']['rosreestr']
    assert rosreestr['found'] is True
    assert rosreestr['error'] is None
    assert rosreestr['house']['cad_number'] == '77:01:000101:1'
    assert rosreestr['house']['info_update_date'] == '2022-04-05'
    assert rosreestr['signals'] == []
    assert rosreestr_stub.calls == ['77:01:000101:1']


async def test_rosreestr_payload_handles_not_found(monkeypatch):
    rosreestr_stub = _RosreestrResolverStub(None)
    use_case = _make_use_case(monkeypatch, rosreestr_stub)

    result = await use_case.execute('г. Москва, ул. Тверская, д. 1')

    rosreestr = result['fias']['rosreestr']
    assert rosreestr['found'] is False
    assert rosreestr['house'] is None
    assert rosreestr['error'] is None
    assert rosreestr['signals'] == []
