"""Доменные сигналы по данным Росреестра."""

from __future__ import annotations

from collections.abc import Iterable

from risks.domain.value_objects.risk_signal import SimpleRiskSignal
from sources.rosreestr.models import RosreestrHouseNormalized


def build_rosreestr_signals(
    *,
    rosreestr: RosreestrHouseNormalized,
    listing_area_total: float | None,
    listing_floors_total: int | None,
) -> list[SimpleRiskSignal]:
    """Построить список сигналов для данных Росреестра."""

    _ = listing_floors_total
    signals: list[SimpleRiskSignal] = []
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
) -> SimpleRiskSignal | None:

    status = rosreestr.is_actual
    if status is True:
        return SimpleRiskSignal(
            code='rosreestr_actual',
            level='good',
            title='Сведения Росреестра актуальны',
            details={'is_actual': True},
        )

    if status is False:
        return SimpleRiskSignal(
            code='rosreestr_not_actual',
            level='warning',
            title='Сведения Росреестра неактуальны',
            details={'is_actual': False},
        )

    return None


def _build_encumbrance_signal(
    rosreestr: RosreestrHouseNormalized,
) -> SimpleRiskSignal | None:

    count = rosreestr.encumbrances_count
    if count is None or count <= 0:
        return None

    return SimpleRiskSignal(
        code='rosreestr_encumbrances',
        level='warning',
        title='Объект обременён',
        details={'encumbrances_count': count},
    )


def _build_area_signal(
    rosreestr_area: float | None,
    listing_area: float | None,
) -> SimpleRiskSignal | None:

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
        return SimpleRiskSignal(
            code='area_mismatch',
            level='warning',
            title='Площадь объявления отличается от Росреестра',
            details=details,
        )

    return SimpleRiskSignal(
        code='area_match',
        level='info',
        title='Площадь объявления близка к Росреестру',
        details=details,
    )


def _build_cad_cost_signal(
    rosreestr: RosreestrHouseNormalized,
) -> SimpleRiskSignal | None:

    if rosreestr.cadastral_value is None:
        return None

    return SimpleRiskSignal(
        code='cad_cost_present',
        level='info',
        title='Доступна кадастровая стоимость',
        details={'cadastral_value': rosreestr.cadastral_value},
    )


def _extend(
    target: list[SimpleRiskSignal],
    items: SimpleRiskSignal | Iterable[SimpleRiskSignal] | None,
) -> None:
    """Добавить в список сигналов новые элементы."""

    if items is None:
        return

    if isinstance(items, SimpleRiskSignal):
        target.append(items)
        return

    target.extend(items)
