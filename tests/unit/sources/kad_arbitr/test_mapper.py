"""Проверка маппинга kad.arbitr.ru."""

from datetime import date

from sources.kad_arbitr.mapper import normalize_case
from sources.kad_arbitr.models import KadArbitrCaseRaw


def test_normalize_case_builds_url_and_date() -> None:
    raw = KadArbitrCaseRaw(
        case_id='123',
        case_number='А40-1/2025',
        court='АС',
        case_type='Иск',
        start_date='2025-01-10',
    )

    result = normalize_case(raw=raw, base_url='https://kad.arbitr.ru')

    assert result.url == 'https://kad.arbitr.ru/Card/123'
    assert result.start_date == date(2025, 1, 10)
