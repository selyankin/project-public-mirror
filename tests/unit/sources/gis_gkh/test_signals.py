"""Тесты сигналов GIS ЖКХ."""

from risks.domain.entities.risk_card import RiskSignal
from sources.gis_gkh.models import GisGkhHouseNormalized
from sources.gis_gkh.signals import build_gis_gkh_signals


def test_signals_include_found():
    house = GisGkhHouseNormalized(
        cadastral_number='77:01:000101:1',
        address='г. Москва',
        house_guid='guid-1',
    )
    signals = build_gis_gkh_signals(house=house)
    assert any(
        isinstance(signal, RiskSignal) and signal.code == 'gis_gkh_found'
        for signal in signals
    )


def test_signals_bad_condition_warning():
    house = GisGkhHouseNormalized(
        cadastral_number='77:01:000101:1',
        condition='аварийное состояние',
    )
    signals = build_gis_gkh_signals(house=house)
    assert any(signal.code == 'gis_gkh_bad_condition' for signal in signals)


def test_signals_management_company():
    house = GisGkhHouseNormalized(
        cadastral_number='77:01:000101:1',
        management_company='УК 1',
    )
    signals = build_gis_gkh_signals(house=house)
    assert any(
        signal.code == 'gis_gkh_management_company' for signal in signals
    )
