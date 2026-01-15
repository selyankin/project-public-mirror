"""Проверка сигналов по исходам kad.arbitr.ru."""

from datetime import date

from sources.kad_arbitr.models import KadArbitrEnrichedCase
from sources.kad_arbitr.signals import build_kad_arbitr_outcome_signals


def test_outcome_signals_bankruptcy() -> None:
    now = date(2026, 1, 10)
    cases = [
        KadArbitrEnrichedCase(
            case_id='1',
            start_date=date(2025, 1, 1),
            target_role='defendant',
            outcome='bankruptcy_observation',
        )
    ]

    signals = build_kad_arbitr_outcome_signals(cases=cases, now=now)

    codes = {signal.code for signal in signals}
    assert 'kad_arbitr_bankruptcy_procedure' in codes


def test_outcome_signals_losses() -> None:
    now = date(2026, 1, 10)
    cases = [
        KadArbitrEnrichedCase(
            case_id='1',
            start_date=date(2025, 6, 1),
            target_role='defendant',
            outcome='satisfied',
        )
    ]

    signals = build_kad_arbitr_outcome_signals(cases=cases, now=now)

    codes = {signal.code for signal in signals}
    assert 'kad_arbitr_losses_last_24m' in codes


def test_outcome_signals_many_loses() -> None:
    now = date(2026, 1, 10)
    cases = [
        KadArbitrEnrichedCase(
            case_id='1',
            start_date=date(2025, 6, 1),
            target_role='defendant',
            outcome='satisfied',
        ),
        KadArbitrEnrichedCase(
            case_id='2',
            start_date=date(2025, 5, 1),
            target_role='defendant',
            outcome='partial',
        ),
        KadArbitrEnrichedCase(
            case_id='3',
            start_date=date(2025, 4, 1),
            target_role='defendant',
            outcome='bankruptcy_competition',
        ),
    ]

    signals = build_kad_arbitr_outcome_signals(cases=cases, now=now)

    codes = {signal.code for signal in signals}
    assert 'kad_arbitr_many_loses_as_defendant' in codes


def test_outcome_signals_unknown_ratio() -> None:
    now = date(2026, 1, 10)
    cases = [
        KadArbitrEnrichedCase(
            case_id=str(idx),
            start_date=date(2025, 1, 1),
            target_role='defendant',
            outcome='unknown',
        )
        for idx in range(5)
    ]

    signals = build_kad_arbitr_outcome_signals(cases=cases, now=now)

    codes = {signal.code for signal in signals}
    assert 'kad_arbitr_outcome_unknown_many' in codes
