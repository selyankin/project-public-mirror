"""Проверка builder сигналов kad.arbitr.ru."""

from datetime import date

from checks.application.kad_arbitr.kad_arbitr_signal_builder import (
    build_kad_arbitr_signals_from_facts,
)
from sources.kad_arbitr.models import (
    KadArbitrEnrichedCase,
    KadArbitrFacts,
)


def test_builder_returns_blocked_signal() -> None:
    facts = KadArbitrFacts(
        status='blocked',
        participant='7701234567',
    )

    signals = build_kad_arbitr_signals_from_facts(facts=facts)

    assert signals[0].code == 'kad_arbitr_source_blocked'


def test_builder_returns_no_cases_found() -> None:
    facts = KadArbitrFacts(
        status='ok',
        participant='7701234567',
        cases=[],
    )

    signals = build_kad_arbitr_signals_from_facts(facts=facts)

    assert signals[0].code == 'kad_arbitr_no_cases_found'


def test_builder_bankruptcy_signal() -> None:
    facts = KadArbitrFacts(
        status='ok',
        participant='7701234567',
        cases=[
            KadArbitrEnrichedCase(
                case_id='1',
                start_date=date(2025, 1, 1),
                outcome='bankruptcy_observation',
            )
        ],
    )

    signals = build_kad_arbitr_signals_from_facts(facts=facts)

    codes = {signal.code for signal in signals}
    assert 'kad_arbitr_bankruptcy_procedure' in codes


def test_builder_many_loses_signal() -> None:
    facts = KadArbitrFacts(
        status='ok',
        participant='7701234567',
        cases=[
            KadArbitrEnrichedCase(
                case_id='1',
                start_date=date(2025, 1, 1),
                target_role='defendant',
                target_role_group='defendant_like',
                outcome='satisfied',
                impact='negative',
            ),
            KadArbitrEnrichedCase(
                case_id='2',
                start_date=date(2025, 1, 2),
                target_role='defendant',
                target_role_group='defendant_like',
                outcome='partial',
                impact='negative',
            ),
            KadArbitrEnrichedCase(
                case_id='3',
                start_date=date(2025, 1, 3),
                target_role='defendant',
                target_role_group='defendant_like',
                outcome='bankruptcy_competition',
                impact='negative',
            ),
        ],
    )

    signals = build_kad_arbitr_signals_from_facts(facts=facts)

    codes = {signal.code for signal in signals}
    assert 'kad_arbitr_many_loses_as_defendant' in codes


def test_builder_unknown_ratio_signal() -> None:
    cases = [
        KadArbitrEnrichedCase(
            case_id=str(idx),
            start_date=date(2025, 1, 1),
            target_role='defendant',
            outcome='unknown',
        )
        for idx in range(5)
    ]
    facts = KadArbitrFacts(
        status='ok',
        participant='7701234567',
        cases=cases,
    )

    signals = build_kad_arbitr_signals_from_facts(
        facts=facts,
        now=date(2026, 1, 10),
    )

    codes = {signal.code for signal in signals}
    assert 'kad_arbitr_outcome_unknown_many' in codes


def test_claim_category_signals_emitted() -> None:
    facts = KadArbitrFacts(
        status='ok',
        participant='7701234567',
        cases=[
            KadArbitrEnrichedCase(
                case_id='1',
                start_date=date(2025, 1, 1),
                claim_categories=['ddu_penalty'],
            ),
            KadArbitrEnrichedCase(
                case_id='2',
                start_date=date(2025, 2, 1),
                claim_categories=['utilities_and_management'],
            ),
        ],
    )

    signals = build_kad_arbitr_signals_from_facts(
        facts=facts,
        now=date(2026, 1, 10),
    )

    codes = {signal.code for signal in signals}
    assert 'kad_arbitr_claims_ddu_penalty' in codes
    assert 'kad_arbitr_claims_utilities_management' in codes


def test_large_amount_signal_emitted() -> None:
    facts = KadArbitrFacts(
        status='ok',
        participant='7701234567',
        cases=[
            KadArbitrEnrichedCase(
                case_id='1',
                start_date=date(2025, 3, 1),
                amounts=[2_000_000],
            )
        ],
    )

    signals = build_kad_arbitr_signals_from_facts(
        facts=facts,
        now=date(2026, 1, 10),
    )

    signal = next(
        item
        for item in signals
        if item.code == 'kad_arbitr_large_claim_amounts'
    )
    assert signal.details['threshold'] == 1_000_000
    assert signal.details['max_amount_overall'] == 2_000_000


def test_out_of_window_cases_ignored() -> None:
    facts = KadArbitrFacts(
        status='ok',
        participant='7701234567',
        cases=[
            KadArbitrEnrichedCase(
                case_id='1',
                start_date=date(2020, 1, 1),
                claim_categories=['ddu_penalty'],
                amounts=[2_000_000],
            )
        ],
    )

    signals = build_kad_arbitr_signals_from_facts(
        facts=facts,
        now=date(2026, 1, 10),
    )

    codes = {signal.code for signal in signals}
    assert 'kad_arbitr_claims_ddu_penalty' not in codes
    assert 'kad_arbitr_large_claim_amounts' not in codes
