"""Преобразование данных kad.arbitr.ru."""

from __future__ import annotations

from sources.kad_arbitr.models import (
    KadArbitrCaseNormalized,
    KadArbitrCaseRaw,
    parse_iso_date,
)


def normalize_case(
    *,
    raw: KadArbitrCaseRaw,
    base_url: str = 'https://kad.arbitr.ru',
) -> KadArbitrCaseNormalized:
    """Нормализовать дело из сырых данных."""

    normalized_url = f'{base_url.rstrip("/")}/Card/{raw.case_id}'
    return KadArbitrCaseNormalized(
        case_id=raw.case_id,
        case_number=raw.case_number,
        court=raw.court,
        case_type=raw.case_type,
        start_date=parse_iso_date(raw.start_date),
        participant_role=None,
        url=normalized_url if raw.case_id else None,
    )


def normalize_cases(
    *,
    raw_cases: list[KadArbitrCaseRaw],
    base_url: str = 'https://kad.arbitr.ru',
) -> list[KadArbitrCaseNormalized]:
    """Нормализовать список дел."""

    return [normalize_case(raw=case, base_url=base_url) for case in raw_cases]
