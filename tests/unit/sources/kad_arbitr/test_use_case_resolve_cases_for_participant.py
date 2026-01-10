"""Проверка use-case kad.arbitr.ru."""

import pytest

from sources.kad_arbitr.models import (
    KadArbitrCaseRaw,
    KadArbitrSearchPayload,
    KadArbitrSearchResponse,
)
from sources.kad_arbitr.use_cases.resolve_cases_for_participant import (
    ResolveKadArbitrCasesForParticipant,
)

pytestmark = pytest.mark.asyncio


class _ClientStub:
    def __init__(self) -> None:
        self.calls: list[int] = []

    async def search_instances(
        self,
        *,
        payload: KadArbitrSearchPayload,
    ) -> KadArbitrSearchResponse:
        self.calls.append(payload.page)
        if payload.page == 1:
            return KadArbitrSearchResponse(
                items=[
                    KadArbitrCaseRaw(
                        case_id='1',
                        case_number='А40-1/2025',
                        case_type='Банкротство',
                        start_date='2025-05-01',
                    )
                ],
                total=2,
                page=1,
                pages=2,
            )
        return KadArbitrSearchResponse(
            items=[
                KadArbitrCaseRaw(
                    case_id='2',
                    case_number='А40-2/2025',
                    start_date='2025-05-02',
                )
            ],
            total=2,
            page=2,
            pages=2,
        )


async def test_use_case_collects_pages_and_signals() -> None:
    client = _ClientStub()
    use_case = ResolveKadArbitrCasesForParticipant(client=client)

    result = await use_case.execute(participant='ООО Ромашка', max_pages=2)

    assert client.calls == [1, 2]
    assert len(result.cases) == 2
    codes = {signal.code for signal in result.signals}
    assert 'kad_arbitr_has_bankruptcy_cases' in codes
