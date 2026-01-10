"""Проверка сигналов kad.arbitr.ru."""

from datetime import date

from sources.kad_arbitr.models import KadArbitrCaseNormalized
from sources.kad_arbitr.signals import build_kad_arbitr_signals


def test_no_cases_signal() -> None:
    signals = build_kad_arbitr_signals(cases=[], now=date(2026, 1, 10))
    assert len(signals) == 1
    assert signals[0].code == 'kad_arbitr_no_cases_found'


def test_bankruptcy_signal() -> None:
    cases = [
        KadArbitrCaseNormalized(
            case_id='1',
            case_number='А40-1/2025',
            case_type='Банкротство',
        )
    ]
    signals = build_kad_arbitr_signals(cases=cases, now=date(2026, 1, 10))
    codes = {signal.code for signal in signals}
    assert 'kad_arbitr_has_bankruptcy_cases' in codes


def test_many_cases_last_12m_signal() -> None:
    now = date(2026, 1, 10)
    cases = [
        KadArbitrCaseNormalized(
            case_id=str(idx),
            case_number=f'А40-{idx}/2025',
            start_date=date(2025, 6, 1),
        )
        for idx in range(10)
    ]
    signals = build_kad_arbitr_signals(cases=cases, now=now)
    codes = {signal.code for signal in signals}
    assert 'kad_arbitr_many_cases_last_12m' in codes


def test_mostly_defendant_signal() -> None:
    cases = [
        KadArbitrCaseNormalized(
            case_id=str(idx),
            case_number=f'А40-{idx}/2025',
            participant_role='defendant',
        )
        for idx in range(4)
    ]
    cases.append(
        KadArbitrCaseNormalized(
            case_id='5',
            case_number='А40-5/2025',
            participant_role='plaintiff',
        )
    )
    signals = build_kad_arbitr_signals(cases=cases, now=date(2026, 1, 10))
    codes = {signal.code for signal in signals}
    assert 'kad_arbitr_mostly_defendant' in codes
