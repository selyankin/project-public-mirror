"""Проверка kad.arbitr payload builder."""

from types import SimpleNamespace

import pytest

from checks.application.use_cases.check_address_sources import (
    build_kad_arbitr_payload,
)
from sources.gis_gkh.models import GisGkhHouseNormalized
from sources.kad_arbitr.models import (
    KadArbitrCaseRaw,
    KadArbitrSearchResponse,
)
from sources.kad_arbitr.stub_client import StubKadArbitrClient

pytestmark = pytest.mark.asyncio


async def test_build_kad_arbitr_payload_returns_payload(monkeypatch) -> None:
    response = KadArbitrSearchResponse(
        items=[
            KadArbitrCaseRaw(
                case_id='1',
                case_number='А40-1/2025',
                case_type='Банкротство',
                start_date='2025-01-10',
            )
        ],
        total=1,
        page=1,
        pages=1,
    )
    client = StubKadArbitrClient(response=response)
    monkeypatch.setattr(
        'checks.application.use_cases.check_address_sources.'
        'build_kad_arbitr_client',
        lambda settings: client,
    )
    settings = SimpleNamespace(
        KAD_ARBITR_BASE_URL='https://kad.arbitr.ru',
    )
    house = GisGkhHouseNormalized(
        cadastral_number='77:01:000101:1',
        management_company='ООО Ромашка ИНН 7701234567',
    )

    payload, signals = await build_kad_arbitr_payload(
        settings=settings,
        gis_gkh_house=house,
    )

    assert payload is not None
    assert payload['status'] == 'ok'
    assert payload['participant'] == '7701234567'
    assert payload['total'] == 1
    assert payload['cases'][0]['case_id'] == '1'
    codes = {signal.code for signal in signals}
    assert 'kad_arbitr_has_bankruptcy_cases' in codes
