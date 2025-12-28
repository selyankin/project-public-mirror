"""Тесты сигналов Росреестра."""

from risks.domain.entities.risk_card import RiskSignal
from sources.rosreestr.models import RosreestrHouseNormalized
from sources.rosreestr.signals import build_rosreestr_signals


def _build_signals(house: RosreestrHouseNormalized, listing_area: float | None):
    return build_rosreestr_signals(
        rosreestr=house,
        listing_area_total=listing_area,
        listing_floors_total=None,
    )


def test_actual_status_signal_good():
    house = RosreestrHouseNormalized(is_actual=True)
    signals = _build_signals(house, None)
    assert any(
        isinstance(signal, RiskSignal) and signal.code == 'rosreestr_actual'
        for signal in signals
    )


def test_encumbrances_signal():
    house = RosreestrHouseNormalized(encumbrances_count=2)
    signals = _build_signals(house, None)
    matches = [
        signal for signal in signals if signal.code == 'rosreestr_encumbrances'
    ]
    assert len(matches) == 1
    assert matches[0].details == {'encumbrances_count': 2}


def test_area_mismatch_warning():
    house = RosreestrHouseNormalized(area_total=80.0)
    signals = _build_signals(house, 100.0)
    assert any(signal.code == 'area_mismatch' for signal in signals)


def test_area_match_info():
    house = RosreestrHouseNormalized(area_total=100.0)
    signals = _build_signals(house, 105.0)
    assert any(signal.code == 'area_match' for signal in signals)
