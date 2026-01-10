"""Проверка use-case kad.arbitr.ru для дома."""

import pytest

from checks.application.use_cases.check_kad_arbitr_for_house import (
    CheckKadArbitrForHouse,
)
from sources.gis_gkh.models import GisGkhHouseNormalized
from sources.kad_arbitr.exceptions import KadArbitrBlockedError
from sources.kad_arbitr.models import (
    KadArbitrCaseRaw,
    KadArbitrSearchPayload,
    KadArbitrSearchResponse,
)

pytestmark = pytest.mark.asyncio


class _KadArbitrClientStub:
    def __init__(
        self,
        response: KadArbitrSearchResponse | None = None,
        error: Exception | None = None,
    ) -> None:
        self._response = response
        self._error = error
        self.calls: list[KadArbitrSearchPayload] = []

    async def search_instances(
        self,
        *,
        payload: KadArbitrSearchPayload,
    ) -> KadArbitrSearchResponse:
        self.calls.append(payload)
        if self._error:
            raise self._error
        return self._response or KadArbitrSearchResponse()


async def test_check_uses_inn_if_present() -> None:
    house = GisGkhHouseNormalized(
        cadastral_number='77:01:000101:1',
        management_company='УК Ромашка ИНН 7701234567',
    )
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
    client = _KadArbitrClientStub(response=response)
    use_case = CheckKadArbitrForHouse(kad_arbitr_client=client)

    result = await use_case.execute(gis_gkh_result=house)

    assert result.status == 'ok'
    assert result.participant_used == '7701234567'
    assert result.cases
    assert client.calls
    codes = {signal.code for signal in result.signals}
    assert 'kad_arbitr_has_bankruptcy_cases' in codes


async def test_check_returns_not_found_if_no_participant() -> None:
    house = GisGkhHouseNormalized(
        cadastral_number='77:01:000101:1',
        management_company='',
    )
    client = _KadArbitrClientStub()
    use_case = CheckKadArbitrForHouse(kad_arbitr_client=client)

    result = await use_case.execute(gis_gkh_result=house)

    assert result.status == 'participant_not_found'
    assert result.cases == []
    assert client.calls == []


async def test_check_returns_blocked_on_error() -> None:
    house = GisGkhHouseNormalized(
        cadastral_number='77:01:000101:1',
        management_company='ООО Ромашка ИНН 7701234567',
    )
    client = _KadArbitrClientStub(error=KadArbitrBlockedError('blocked'))
    use_case = CheckKadArbitrForHouse(kad_arbitr_client=client)

    result = await use_case.execute(gis_gkh_result=house)

    assert result.status == 'blocked'
    assert result.cases == []
