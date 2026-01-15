"""Проверка use-case получения актов kad.arbitr.ru."""

import pytest

from sources.kad_arbitr.stub_client import StubKadArbitrClient
from sources.kad_arbitr.use_cases.resolve_case_acts import (
    ResolveKadArbitrCaseActs,
)

pytestmark = pytest.mark.asyncio


async def test_resolve_case_acts_returns_acts() -> None:
    html = (
        '<html><body>'
        '<a href="https://kad.arbitr.ru/Document/Pdf/123/456/act.pdf'
        '?isAddStamp=True">Решение 10.01.2026</a>'
        '<a href="https://kad.arbitr.ru/Document/Pdf/123/789/act2.pdf'
        '?isAddStamp=True">Определение 05.12.2025</a>'
        '</body></html>'
    )
    client = StubKadArbitrClient(
        case_acts_cards_by_id={'123': html},
    )
    use_case = ResolveKadArbitrCaseActs(client=client)

    result = await use_case.execute(case_id='123')

    assert len(result.acts) == 2
    assert result.acts[0].pdf_url is not None
