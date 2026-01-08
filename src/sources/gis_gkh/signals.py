"""Сигналы риска на основе GIS ЖКХ."""

from __future__ import annotations

from collections.abc import Iterable

from risks.domain.constants.enums.risk import SignalSeverity
from risks.domain.entities.risk_card import RiskSignal
from sources.gis_gkh.models import GisGkhHouseNormalized


def build_gis_gkh_signals(
    *,
    house: GisGkhHouseNormalized,
) -> list[RiskSignal]:
    """Построить сигналы для данных GIS ЖКХ."""

    signals: list[RiskSignal] = []
    _extend(signals, _build_found_signal(house))
    _extend(signals, _build_condition_signal(house))
    _extend(signals, _build_management_signal(house))

    return signals


def _build_found_signal(house: GisGkhHouseNormalized) -> RiskSignal | None:
    if not (house.address or house.house_guid):
        return None

    return _make_signal(
        code='gis_gkh_found',
        title='Объект найден в GIS ЖКХ',
        level='info',
        details={
            'cadastral_number': house.cadastral_number,
            'address': house.address,
        },
    )


def _build_condition_signal(
    house: GisGkhHouseNormalized,
) -> RiskSignal | None:
    condition = (house.condition or '').lower()
    if 'авар' in condition or 'ветх' in condition:
        return _make_signal(
            code='gis_gkh_bad_condition',
            title='Состояние дома неудовлетворительное',
            level='warning',
            details={'condition': house.condition},
        )

    return None


def _build_management_signal(
    house: GisGkhHouseNormalized,
) -> RiskSignal | None:

    if not house.management_company:
        return None

    return _make_signal(
        code='gis_gkh_management_company',
        title='У дома есть управляющая организация',
        level='info',
        details={'management_company': house.management_company},
    )


def _make_signal(
    *,
    code: str,
    title: str,
    level: str,
    details: dict[str, object],
) -> RiskSignal:

    return RiskSignal(
        {
            'code': code,
            'title': title,
            'description': title,
            'severity': int(_severity_from_level(level)),
            'evidence_refs': [],
            'level': level,
            'details': details,
        }
    )


def _severity_from_level(level: str) -> SignalSeverity:
    mapping = {
        'info': SignalSeverity.info,
        'good': SignalSeverity.info,
        'warning': SignalSeverity.low,
    }
    return mapping.get(level, SignalSeverity.info)


def _extend(
    target: list[RiskSignal],
    items: RiskSignal | Iterable[RiskSignal] | None,
) -> None:
    """Добавить сигнал или список в коллекцию."""

    if items is None:
        return

    if isinstance(items, RiskSignal):
        target.append(items)
        return

    target.extend(items)
