"""Тест use-case GIS ЖКХ."""

import pytest

from sources.gis_gkh.models import GisGkhHouseNormalized
from sources.gis_gkh.stub_client import StubGisGkhClient
from sources.gis_gkh.use_cases.resolve_house_by_cadastral import (
    ResolveGisGkhHouseByCadastralUseCase,
)

pytestmark = pytest.mark.asyncio


async def test_use_case_returns_first_house():
    house = GisGkhHouseNormalized(
        cadastral_number='77:01:000101:1',
        address='г. Москва, ул. Тверская, д. 1',
    )
    use_case = ResolveGisGkhHouseByCadastralUseCase(
        client=StubGisGkhClient(result=house),
    )

    result = await use_case.execute(
        cadastral_number='77:01:000101:1',
        region_code='77',
    )

    assert result is house


async def test_use_case_returns_none_for_miss():
    house = GisGkhHouseNormalized(
        cadastral_number='77:01:000101:1',
        address='г. Москва, ул. Тверская, д. 1',
    )
    use_case = ResolveGisGkhHouseByCadastralUseCase(
        client=StubGisGkhClient(result=house),
    )

    result = await use_case.execute(
        cadastral_number='00:00:000000:0',
        region_code='77',
    )

    assert result is None
