"""Проверка расширенного payload ФИАС."""

from datetime import UTC, datetime

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
            fias_houseguid='house-guid-1',
            fias_aoguid='ao-guid-1',
            gar_house_id='gar-house-1',
            gar_object_id='gar-object-1',
            postal_code='101000',
            oktmo='45000000',
            okato='45000000000',
            region_code='77',
            cadastral_number='77:01:000101',
            status='active',
            is_active=True,
            updated_at=datetime(2024, 5, 1, tzinfo=UTC),
        )


@pytest.fixture(autouse=True)
def listing_resolver_stub(monkeypatch):
    stub = _ListingResolverStub()
    monkeypatch.setattr(
        'checks.application.use_cases.check_address.'
        'get_listing_resolver_use_case',
        lambda: stub,
    )
    return stub


async def test_fias_payload_contains_house_block():
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
    )

    result = await use_case.execute('г. Москва, ул. Тверская, д. 1')

    house = result['fias']['house']
    assert house['house_key'] == 'house-guid-1'
    assert house['fias_houseguid'] == 'house-guid-1'
    assert house['gar_house_id'] == 'gar-house-1'
    assert house['postal_code'] == '101000'
    assert house['region_code'] == '77'
