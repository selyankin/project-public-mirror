"""Получение данных ФИАС и источников."""

from __future__ import annotations

import asyncio
import inspect
import logging
from typing import Any

from checks.application.ports.fias_client import FiasClient
from checks.application.use_cases.check_address_payloads import (
    build_house_payload,
    gis_gkh_house_to_payload,
    rosreestr_house_to_payload,
)
from checks.application.use_cases.check_kad_arbitr_for_house import (
    CheckKadArbitrForHouse,
)
from checks.infrastructure.gis_gkh_resolver_container import (
    get_gis_gkh_resolver_use_case,
)
from checks.infrastructure.rosreestr_resolver_container import (
    get_rosreestr_resolver_use_case,
)
from risks.domain.entities.risk_card import RiskSignal
from shared.kernel.kad_arbitr_client_factory import build_kad_arbitr_client
from shared.kernel.settings import Settings
from sources.gis_gkh.models import GisGkhHouseNormalized
from sources.rosreestr.models import RosreestrHouseNormalized

logger = logging.getLogger(__name__)


async def fetch_fias_data(
    *,
    fias_client: FiasClient,
    fias_mode: str,
    query: str,
    settings: Settings | None,
) -> tuple[
    dict[str, Any] | None,
    dict[str, Any] | None,
    RosreestrHouseNormalized | None,
    dict[str, Any] | None,
    GisGkhHouseNormalized | None,
    dict[str, Any] | None,
    dict[str, Any] | None,
    list[RiskSignal],
]:
    """Получить нормализацию из ФИАС и источников."""

    try:
        normalized = await fias_client.normalize_address(query)
    except Exception as exc:
        logger.warning(
            'fias_normalize_failed mode=%s query=%s error=%s',
            fias_mode,
            query[:80],
            exc,
        )
        return None, None, None, None, None, None, None, []

    if normalized is None:
        return None, None, None, None, None, None, None, []

    public_payload = {
        'source_query': normalized.source_query,
        'normalized': normalized.normalized,
        'fias_id': normalized.fias_id,
        'confidence': normalized.confidence,
    }
    house_payload = build_house_payload(
        normalized=normalized,
        listing=None,
    )
    if house_payload:
        public_payload['house'] = house_payload

    target_number = (
        house_payload.get('cadastral_number') if house_payload else None
    )
    if not target_number:
        target_number = normalized.cadastral_number

    (
        rosreestr_payload,
        rosreestr_house,
    ) = await build_rosreestr_payload(
        settings=settings,
        target_number=target_number,
    )

    (
        gis_gkh_payload,
        gis_gkh_house,
    ) = await build_gis_gkh_payload(
        settings=settings,
        target_number=target_number,
        region_code=normalized.region_code,
        house_payload=house_payload,
    )
    (
        kad_arbitr_payload,
        kad_arbitr_signals,
    ) = await build_kad_arbitr_payload(
        settings=settings,
        gis_gkh_house=gis_gkh_house,
    )

    return (
        public_payload,
        normalized.raw,
        rosreestr_house,
        rosreestr_payload,
        gis_gkh_house,
        gis_gkh_payload,
        kad_arbitr_payload,
        kad_arbitr_signals,
    )


async def build_rosreestr_payload(
    *,
    settings: Settings | None,
    target_number: str | None,
) -> tuple[dict[str, Any] | None, RosreestrHouseNormalized | None]:
    """Получить данные Росреестра и собрать payload."""

    if not settings:
        return None, None

    if not target_number:
        return None, None

    resolver = get_rosreestr_resolver_use_case(settings)
    try:
        rosreestr_house = await asyncio.to_thread(
            resolver.execute,
            cadastral_number=target_number,
        )
    except Exception as exc:
        logger.info(
            'rosreestr_resolver_failed cadastral=%s error=%s',
            target_number,
            exc,
        )
        return (
            {
                'found': False,
                'house': None,
                'error': exc.__class__.__name__,
                'signals': [],
            },
            None,
        )

    if rosreestr_house is None:
        return (
            {
                'found': False,
                'house': None,
                'error': None,
                'signals': [],
            },
            None,
        )

    return (
        {
            'found': True,
            'house': rosreestr_house_to_payload(rosreestr_house),
            'error': None,
            'signals': [],
        },
        rosreestr_house,
    )


async def build_gis_gkh_payload(
    *,
    settings: Settings | None,
    target_number: str | None,
    region_code: str | None,
    house_payload: dict[str, Any] | None,
) -> tuple[dict[str, Any] | None, GisGkhHouseNormalized | None]:
    """Получить данные GIS ЖКХ и собрать payload."""

    if not settings:
        return None, None

    resolved_region = region_code
    if not resolved_region and house_payload:
        resolved_region = house_payload.get('region_code')

    if not target_number or not resolved_region:
        return None, None

    resolver = get_gis_gkh_resolver_use_case(settings)
    try:
        gis_gkh_house = await resolver.execute(
            cadastral_number=target_number,
            region_code=resolved_region,
        )
    except Exception as exc:
        logger.info(
            'gis_gkh_resolver_failed cadastral=%s error=%s',
            target_number,
            exc,
        )
        return (
            {
                'found': False,
                'house': None,
                'error': exc.__class__.__name__,
                'signals': [],
            },
            None,
        )

    if gis_gkh_house is None:
        return (
            {
                'found': False,
                'house': None,
                'error': None,
                'signals': [],
            },
            None,
        )

    return (
        {
            'found': True,
            'house': gis_gkh_house_to_payload(gis_gkh_house),
            'error': None,
            'signals': [],
        },
        gis_gkh_house,
    )


async def build_kad_arbitr_payload(
    *,
    settings: Settings | None,
    gis_gkh_house: GisGkhHouseNormalized | None,
) -> tuple[dict[str, Any] | None, list[RiskSignal]]:
    """Получить данные kad.arbitr.ru и собрать payload."""

    if not settings or gis_gkh_house is None:
        return None, []

    client = build_kad_arbitr_client(settings=settings)
    use_case = CheckKadArbitrForHouse(
        kad_arbitr_client=client,
        base_url=settings.KAD_ARBITR_BASE_URL,
    )
    max_pages = getattr(settings, 'KAD_ARBITR_MAX_PAGES', 3)
    try:
        result = await use_case.execute(
            gis_gkh_result=gis_gkh_house,
            max_pages=max_pages,
        )
    finally:
        close_method = getattr(client, 'close', None)
        if callable(close_method):
            result_close = close_method()
            if inspect.isawaitable(result_close):
                await result_close

    payload = {
        'status': result.status,
        'participant': result.participant_used,
        'total': result.total,
        'cases': [
            {
                'case_id': case.case_id,
                'case_number': case.case_number,
                'court': case.court,
                'case_type': case.case_type,
                'start_date': (
                    case.start_date.isoformat() if case.start_date else None
                ),
                'url': case.url,
            }
            for case in result.cases
        ],
        'signals': [signal.to_dict() for signal in result.signals],
    }

    return payload, result.signals
