"""Тесты сигналов Росреестра."""

from sources.rosreestr.models import RosreestrHouseNormalized
from sources.rosreestr.signals import build_rosreestr_signals


def test_actual_status_signal_good():
    house = RosreestrHouseNormalized(is_actual=True)
    signals = build_rosreestr_signals(
        rosreestr=house,
        listing_area_total=None,
        listing_floors_total=None,
    )
    assert any(signal.code == 'rosreestr_actual' for signal in signals)


def test_encumbrances_signal():
    house = RosreestrHouseNormalized(encumbrances_count=2)
    signals = build_rosreestr_signals(
        rosreestr=house,
        listing_area_total=None,
        listing_floors_total=None,
    )
    enc_signals = [
        signal for signal in signals if signal.code == 'rosreestr_encumbrances'
    ]
    assert len(enc_signals) == 1
    assert enc_signals[0].details == {'encumbrances_count': 2}


def test_area_mismatch_warning():
    house = RosreestrHouseNormalized(area_total=80.0)
    signals = build_rosreestr_signals(
        rosreestr=house,
        listing_area_total=100.0,
        listing_floors_total=None,
    )
    codes = {signal.code for signal in signals}
    assert 'area_mismatch' in codes


def test_area_match_info():
    house = RosreestrHouseNormalized(area_total=100.0)
    signals = build_rosreestr_signals(
        rosreestr=house,
        listing_area_total=105.0,
        listing_floors_total=None,
    )
    codes = {signal.code for signal in signals}
    assert 'area_match' in codes
