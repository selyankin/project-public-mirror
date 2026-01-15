"""Проверка use-case получения карточки дела kad.arbitr.ru."""

import pytest

from sources.kad_arbitr.stub_client import StubKadArbitrClient
from sources.kad_arbitr.use_cases.resolve_case_details import (
    ResolveKadArbitrCaseDetails,
)

pytestmark = pytest.mark.asyncio


async def test_resolve_case_details_returns_parsed_result() -> None:
    html = (
        '<html><body>'
        '<div>Дело № А40-1/2025</div>'
        '<div>Истец: ООО Ромашка ИНН 7701234567</div>'
        '</body></html>'
    )
    client = StubKadArbitrClient(
        case_cards_by_id={'case-1': html},
    )
    use_case = ResolveKadArbitrCaseDetails(client=client)

    result = await use_case.execute(case_id='case-1')

    assert result.case_id == 'case-1'
    assert result.case_number == 'А40-1/2025'
    assert result.participants[0].inn == '7701234567'
