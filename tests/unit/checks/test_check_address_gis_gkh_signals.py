"""Проверка сигналов GIS ЖКХ в payload проверки."""

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
from sources.gis_gkh.models import GisGkhHouseNormalized

pytestmark = pytest.mark.asyncio


class _FiasClientStub:
    async def normalize_address(self, query: str) -> NormalizedAddress | None:
        return NormalizedAddress(
            source_query=query,
            normalized='г. Москва, ул. Тверская, д. 1',
            fias_id='fias-main',
            confidence=0.95,
            raw={'query': query},
            cadastral_number='77:01:000101:1',
            region_code='77',
        )


class _RosreestrResolverStub:
    def execute(self, *, cadastral_number: str):
        return None


class _GisGkhResolverStub:
    def __init__(self, house: GisGkhHouseNormalized | None) -> None:
        self._house = house

    async def execute(
        self,
        *,
        cadastral_number: str,
        region_code: str,
    ) -> GisGkhHouseNormalized | None:
        return self._house


def _make_use_case(monkeypatch, gis_gkh_house: GisGkhHouseNormalized):
    monkeypatch.setattr(
        'checks.infrastructure.rosreestr_resolver_container.'
        'get_rosreestr_resolver_use_case',
        lambda settings: _RosreestrResolverStub(),
    )
    monkeypatch.setattr(
        'checks.infrastructure.gis_gkh_resolver_container.'
        'get_gis_gkh_resolver_use_case',
        lambda settings: _GisGkhResolverStub(gis_gkh_house),
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
        settings=SimpleNamespace(
            ROSREESTR_MODE='stub',
            GIS_GKH_MODE='stub',
        ),
    )


async def test_gis_gkh_signals_in_response(monkeypatch):
    house = GisGkhHouseNormalized(
        cadastral_number='77:01:000101:1',
        address='г. Москва, ул. Тверская, д. 1',
        house_guid='gis-house-1',
        management_company='УК Тест',
        condition='Аварийное',
    )
    use_case = _make_use_case(monkeypatch, house)

    result = await use_case.execute('г. Москва, ул. Тверская, д. 1')

    gis_gkh_payload = result['sources']['gis_gkh']
    assert gis_gkh_payload['found'] is True
    assert gis_gkh_payload['house']['house_guid'] == 'gis-house-1'
    payload_codes = {signal['code'] for signal in gis_gkh_payload['signals']}
    assert 'gis_gkh_found' in payload_codes
    assert 'gis_gkh_bad_condition' in payload_codes
    assert 'gis_gkh_management_company' in payload_codes

    risk_codes = {signal['code'] for signal in result['signals']}
    assert 'gis_gkh_found' in risk_codes
