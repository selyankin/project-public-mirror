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
