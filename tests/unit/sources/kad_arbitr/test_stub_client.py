"""Проверка stub клиента kad.arbitr.ru."""

import pytest

from sources.kad_arbitr.models import (
    KadArbitrCaseRaw,
    KadArbitrSearchPayload,
    KadArbitrSearchResponse,
)
from sources.kad_arbitr.stub_client import StubKadArbitrClient

pytestmark = pytest.mark.asyncio


async def test_stub_returns_empty_response() -> None:
    client = StubKadArbitrClient()
    payload = KadArbitrSearchPayload(page=3)

    result = await client.search_instances(payload=payload)

    assert result.page == 3
    assert result.total == 0
    assert result.items == []


async def test_stub_returns_provided_response() -> None:
    response = KadArbitrSearchResponse(
        items=[
            KadArbitrCaseRaw(
                case_id='case-1',
                case_number='А40-1/2024',
            ),
        ],
        total=1,
        page=1,
        pages=1,
    )
    client = StubKadArbitrClient(response=response)

    result = await client.search_instances(
        payload=KadArbitrSearchPayload(),
    )

    assert result is response


async def test_stub_returns_case_card_html() -> None:
    html = '<html><body>card</body></html>'
    client = StubKadArbitrClient(
        case_cards_by_id={'case-1': html},
    )

    result = await client.get_case_card_html(case_id='case-1')

    assert result == html


async def test_stub_returns_case_acts_html() -> None:
    html = '<html><body>acts</body></html>'
    client = StubKadArbitrClient(
        case_acts_cards_by_id={'case-1': html},
    )

    result = await client.get_case_acts_html(case_id='case-1')

    assert result == html
