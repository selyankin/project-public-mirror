"""Доменные сигналы по данным Росреестра."""

from __future__ import annotations

from collections.abc import Iterable

from risks.domain.constants.enums.risk import SignalSeverity
from risks.domain.entities.risk_card import RiskSignal
from sources.rosreestr.models import RosreestrHouseNormalized


def build_rosreestr_signals(
    *,
    rosreestr: RosreestrHouseNormalized,
    listing_area_total: float | None,
    listing_floors_total: int | None,
) -> list[RiskSignal]:
    """Построить список сигналов для данных Росреестра."""

    _ = listing_floors_total
    signals: list[RiskSignal] = []
    _extend(signals, _build_actual_status_signal(rosreestr))
    _extend(signals, _build_encumbrance_signal(rosreestr))
    _extend(
        signals,
        _build_area_signal(
            rosreestr.area_total,
            listing_area_total,
        ),
    )
    _extend(signals, _build_cad_cost_signal(rosreestr))

    return signals


def _build_actual_status_signal(
    rosreestr: RosreestrHouseNormalized,
) -> RiskSignal | None:

    status = rosreestr.is_actual
    if status is True:
        return _make_signal(
            code='rosreestr_actual',
            title='Сведения Росреестра актуальны',
            level='good',
            details={'is_actual': True},
        )

    if status is False:
        return _make_signal(
            code='rosreestr_not_actual',
            title='Сведения Росреестра неактуальны',
            level='warning',
            details={'is_actual': False},
        )

    return None


def _build_encumbrance_signal(
    rosreestr: RosreestrHouseNormalized,
) -> RiskSignal | None:

    count = rosreestr.encumbrances_count
    if count is None or count <= 0:
        return None

    return _make_signal(
        code='rosreestr_encumbrances',
        title='Объект обременён',
        level='warning',
        details={'encumbrances_count': count},
    )


def _build_area_signal(
    rosreestr_area: float | None,
    listing_area: float | None,
) -> RiskSignal | None:

    if rosreestr_area is None or rosreestr_area <= 0:
        return None

    if listing_area is None or listing_area <= 0:
        return None

    delta = abs(listing_area - rosreestr_area) / rosreestr_area
    details = {
        'rosreestr_area_total': rosreestr_area,
        'listing_area_total': listing_area,
        'delta_pct': delta,
    }

    if delta >= 0.15:
        return _make_signal(
            code='area_mismatch',
            title='Площадь объявления отличается от Росреестра',
            level='warning',
            details=details,
        )

    return _make_signal(
        code='area_match',
        title='Площадь объявления близка к Росреестру',
        level='info',
        details=details,
    )


def _build_cad_cost_signal(
    rosreestr: RosreestrHouseNormalized,
) -> RiskSignal | None:

    if rosreestr.cadastral_value is None:
        return None

    return _make_signal(
        code='cad_cost_present',
        title='Доступна кадастровая стоимость',
        level='info',
        details={'cadastral_value': rosreestr.cadastral_value},
    )


def _make_signal(
    *,
    code: str,
    title: str,
    level: str,
    details: dict[str, object],
) -> RiskSignal:

    severity = _severity_from_level(level)
    return RiskSignal(
        {
            'code': code,
            'title': title,
            'description': title,
            'severity': int(severity),
            'evidence_refs': [],
            'level': level,
            'details': details,
        }
    )


def _severity_from_level(level: str) -> SignalSeverity:
    mapping = {
        'good': SignalSeverity.info,
        'info': SignalSeverity.info,
        'warning': SignalSeverity.low,
    }
    return mapping.get(level, SignalSeverity.info)


def _extend(
    target: list[RiskSignal],
    items: RiskSignal | Iterable[RiskSignal] | None,
) -> None:
    """Добавить в список сигналов новые элементы."""

    if items is None:
        return

    if isinstance(items, RiskSignal):
        target.append(items)
        return

    target.extend(items)
