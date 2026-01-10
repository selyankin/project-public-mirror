"""Вспомогательные функции для сигналов проверки."""

from __future__ import annotations

import json
from typing import Any

from risks.domain.entities.risk_card import RiskSignal
from risks.domain.signals_catalog import get_signal_definition
from sources.gis_gkh.models import GisGkhHouseNormalized
from sources.gis_gkh.signals import build_gis_gkh_signals
from sources.rosreestr.models import RosreestrHouseNormalized
from sources.rosreestr.signals import build_rosreestr_signals


def sanitize_input_value(value: str) -> str:
    """Свести строку к единообразному виду для ключа кэша."""

    return ' '.join(value.strip().split())


def build_single_signal(
    *,
    code: str,
    evidence: tuple[str, ...],
    details: dict[str, Any] | None = None,
) -> RiskSignal:
    """Создать единичный сигнал по коду справочника."""

    definition = get_signal_definition(code)
    payload = {
        'code': definition.code,
        'title': definition.title,
        'description': definition.description,
        'severity': int(definition.severity),
        'evidence_refs': evidence,
    }
    if details:
        payload['details'] = details

    return RiskSignal(payload)


def merge_signals(
    *,
    base: tuple[RiskSignal, ...],
    extra: tuple[RiskSignal, ...],
) -> tuple[RiskSignal, ...]:
    """Слить наборы сигналов с дедупликацией."""

    if not extra:
        return base

    def _fingerprint(signal: RiskSignal) -> str:
        level = signal.level or ''
        details = ''
        if signal.details is not None:
            try:
                details = json.dumps(
                    signal.details,
                    sort_keys=True,
                    ensure_ascii=False,
                )
            except TypeError:
                details = str(signal.details)
        return f'{signal.code}|{level}|{details}'

    existing = {_fingerprint(signal) for signal in base}
    merged = list(base)
    for signal in extra:
        fingerprint = _fingerprint(signal)
        if fingerprint in existing:
            continue
        existing.add(fingerprint)
        merged.append(signal)

    return tuple(merged)


def apply_rosreestr_signals(
    *,
    rosreestr_payload: dict[str, Any] | None,
    house: RosreestrHouseNormalized | None,
    listing_payload: dict[str, Any] | None,
) -> tuple[RiskSignal, ...]:
    """Добавить сигналы Росреестра к payload."""

    if not rosreestr_payload:
        return ()

    listing_area = (
        listing_payload.get('area_total') if listing_payload else None
    )
    listing_floors = (
        listing_payload.get('floors_total') if listing_payload else None
    )
    if house is None:
        rosreestr_payload.setdefault('signals', [])
        return ()

    signals = build_rosreestr_signals(
        rosreestr=house,
        listing_area_total=listing_area,
        listing_floors_total=listing_floors,
    )
    rosreestr_payload['signals'] = [signal.to_dict() for signal in signals]
    return tuple(signals)


def apply_gis_gkh_signals(
    *,
    gis_gkh_payload: dict[str, Any] | None,
    house: GisGkhHouseNormalized | None,
    listing_payload: dict[str, Any] | None,
) -> tuple[RiskSignal, ...]:
    """Добавить сигналы GIS ЖКХ к payload."""

    del listing_payload
    if not gis_gkh_payload:
        return ()

    if house is None:
        gis_gkh_payload.setdefault('signals', [])
        return ()

    signals = build_gis_gkh_signals(house=house)
    gis_gkh_payload['signals'] = [signal.to_dict() for signal in signals]
    return tuple(signals)
