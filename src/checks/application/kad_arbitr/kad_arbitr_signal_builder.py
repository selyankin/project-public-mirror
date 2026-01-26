"""Построение сигналов kad.arbitr.ru на уровне checks."""

from __future__ import annotations

from datetime import date, timedelta

from risks.domain.constants.enums.risk import SignalSeverity
from risks.domain.entities.risk_card import RiskSignal
from risks.domain.signals_catalog import get_signal_definition
from sources.kad_arbitr.models import (
    KadArbitrEnrichedCase,
    KadArbitrFacts,
    is_bankruptcy_outcome,
)

WINDOW_MONTHS = 24
LARGE_AMOUNT_THRESHOLD = 1_000_000
MAX_EXAMPLES = 3


def build_kad_arbitr_signals_from_facts(
    *,
    facts: KadArbitrFacts,
    now: date | None = None,
) -> list[RiskSignal]:
    """Собрать сигналы kad.arbitr.ru из фактов."""

    if facts.status == 'blocked':
        return [_make_status_signal('kad_arbitr_source_blocked')]
    if facts.status == 'error':
        return [_make_status_signal('kad_arbitr_source_error')]

    if not facts.cases:
        return [_make_signal(code='kad_arbitr_no_cases_found', details={})]

    signals: list[RiskSignal] = []
    current = now or date.today()
    cutoff_24m = current - timedelta(days=730)
    cutoff_12m = current - timedelta(days=365)
    window_cases = [
        case
        for case in facts.cases
        if case.start_date and case.start_date >= cutoff_24m
    ]
    considered = window_cases or facts.cases

    losses = _count_losses_by_impact(considered)
    losses_defendant = _count_losses_by_group(
        considered,
        group='defendant_like',
    )
    losses_plaintiff = _count_losses_by_group(
        considered,
        group='plaintiff_like',
    )
    unknown_count = len(
        [case for case in considered if case.outcome == 'unknown']
    )
    unknown_impact_count = len(
        [case for case in considered if case.impact == 'unknown']
    )

    if _has_bankruptcy_case_type(facts.cases):
        signals.append(
            _make_signal(
                code='kad_arbitr_has_bankruptcy_cases',
                details=_details(
                    cases=considered,
                    cutoff=cutoff_24m,
                    losses=losses,
                    unknown_count=unknown_count,
                    losses_defendant=losses_defendant,
                    losses_plaintiff=losses_plaintiff,
                    unknown_impact_count=unknown_impact_count,
                ),
            )
        )

    if any(is_bankruptcy_outcome(case.outcome) for case in considered):
        signals.append(
            _make_signal(
                code='kad_arbitr_bankruptcy_procedure',
                details=_details(
                    cases=considered,
                    cutoff=cutoff_24m,
                    losses=losses,
                    unknown_count=unknown_count,
                    losses_defendant=losses_defendant,
                    losses_plaintiff=losses_plaintiff,
                    unknown_impact_count=unknown_impact_count,
                ),
            )
        )

    if losses >= 1:
        signals.append(
            _make_signal(
                code='kad_arbitr_losses_last_24m',
                details=_details(
                    cases=considered,
                    cutoff=cutoff_24m,
                    losses=losses,
                    unknown_count=unknown_count,
                    losses_defendant=losses_defendant,
                    losses_plaintiff=losses_plaintiff,
                    unknown_impact_count=unknown_impact_count,
                ),
            )
        )

    if losses_defendant >= 3:
        signals.append(
            _make_signal(
                code='kad_arbitr_many_loses_as_defendant',
                details=_details(
                    cases=considered,
                    cutoff=cutoff_24m,
                    losses=losses_defendant,
                    unknown_count=unknown_count,
                    losses_defendant=losses_defendant,
                    losses_plaintiff=losses_plaintiff,
                    unknown_impact_count=unknown_impact_count,
                ),
            )
        )

    if len(considered) >= 5:
        ratio = unknown_count / len(considered)
        if ratio >= 0.6:
            signals.append(
                _make_signal(
                    code='kad_arbitr_outcome_unknown_many',
                    details=_details(
                        cases=considered,
                        cutoff=cutoff_24m,
                        losses=losses,
                        unknown_count=unknown_count,
                        losses_defendant=losses_defendant,
                        losses_plaintiff=losses_plaintiff,
                        unknown_impact_count=unknown_impact_count,
                    ),
                )
            )

    recent_cases = [
        case
        for case in facts.cases
        if case.start_date and case.start_date >= cutoff_12m
    ]
    if len(recent_cases) >= 10:
        if len(recent_cases) >= 25:
            severity = SignalSeverity.high
        else:
            severity = SignalSeverity.medium
        signals.append(
            _make_signal(
                code='kad_arbitr_many_cases_last_12m',
                details={
                    'count': len(recent_cases),
                    'cutoff': cutoff_12m.isoformat(),
                },
                severity=severity,
            )
        )

    if _mostly_defendant(facts.cases):
        signals.append(
            _make_signal(
                code='kad_arbitr_mostly_defendant',
                details={
                    'ratio': _defendant_ratio(facts.cases),
                    'total': len(facts.cases),
                },
            )
        )

    category_signals = _build_category_signals(
        cases=facts.cases,
        now=current,
    )
    signals.extend(category_signals)

    amount_signal = _build_large_amount_signal(
        cases=facts.cases,
        now=current,
    )
    if amount_signal is not None:
        signals.append(amount_signal)

    return signals


def _has_bankruptcy_case_type(cases: list[KadArbitrEnrichedCase]) -> bool:
    for case in cases:
        case_type = (case.case_type or '').lower()
        if 'банкрот' in case_type:
            return True
    return False


def _count_losses_by_impact(cases: list[KadArbitrEnrichedCase]) -> int:
    losses = 0
    for case in cases:
        if case.impact == 'negative':
            losses += 1
    return losses


def _count_losses_by_group(
    cases: list[KadArbitrEnrichedCase],
    *,
    group: str,
) -> int:
    losses = 0
    for case in cases:
        if case.target_role_group == group and case.impact == 'negative':
            losses += 1
    return losses


def _mostly_defendant(cases: list[KadArbitrEnrichedCase]) -> bool:
    if len(cases) < 5:
        return False

    ratio = _defendant_ratio(cases)
    return ratio >= 0.7


def _defendant_ratio(cases: list[KadArbitrEnrichedCase]) -> float:
    defendant_cases = [
        case for case in cases if case.target_role_group == 'defendant_like'
    ]
    return len(defendant_cases) / len(cases) if cases else 0.0


def _details(
    *,
    cases: list[KadArbitrEnrichedCase],
    cutoff: date,
    losses: int,
    unknown_count: int,
    losses_defendant: int,
    losses_plaintiff: int,
    unknown_impact_count: int,
) -> dict[str, object]:
    return {
        'total_considered': len(cases),
        'losses_count': losses,
        'losses_defendant_like_count': losses_defendant,
        'losses_plaintiff_like_count': losses_plaintiff,
        'unknown_count': unknown_count,
        'unknown_impact_count': unknown_impact_count,
        'window_months': WINDOW_MONTHS,
        'cutoff': cutoff.isoformat(),
        'examples': [
            {
                'case_id': case.case_id,
                'case_number': case.case_number or case.case_id,
            }
            for case in cases[:MAX_EXAMPLES]
        ],
    }


def _make_status_signal(code: str) -> RiskSignal:
    return _make_signal(code=code, details={'source': 'kad_arbitr'})


def _make_signal(
    *,
    code: str,
    details: dict[str, object],
    severity: SignalSeverity | None = None,
) -> RiskSignal:
    definition = get_signal_definition(code)
    return RiskSignal(
        {
            'code': definition.code,
            'title': definition.title,
            'description': definition.description,
            'severity': int(severity or definition.severity),
            'evidence_refs': [],
            'details': details,
        }
    )


def _build_category_signals(
    *,
    cases: list[KadArbitrEnrichedCase],
    now: date,
) -> list[RiskSignal]:
    signals: list[RiskSignal] = []

    category_map = {
        'construction_quality': 'kad_arbitr_claims_construction_quality',
        'ddu_penalty': 'kad_arbitr_claims_ddu_penalty',
        'utilities_and_management': ('kad_arbitr_claims_utilities_management'),
        'land_and_property': 'kad_arbitr_claims_land_property',
        'corporate_dispute': 'kad_arbitr_claims_corporate',
    }

    for category, signal_code in category_map.items():
        matched = [
            case
            for case in cases
            if _in_window(case, now=now, months=WINDOW_MONTHS)
            and category in (case.claim_categories or [])
        ]
        if not matched:
            continue
        signals.append(
            _make_signal(
                code=signal_code,
                details={
                    'category': category,
                    'window_months': WINDOW_MONTHS,
                    'cases_count': len(matched),
                    'examples': _collect_examples(matched),
                },
            )
        )

    return signals


def _build_large_amount_signal(
    *,
    cases: list[KadArbitrEnrichedCase],
    now: date,
) -> RiskSignal | None:
    matched: list[tuple[KadArbitrEnrichedCase, int]] = []
    for case in cases:
        if not _in_window(case, now=now, months=WINDOW_MONTHS):
            continue
        if not case.amounts:
            continue
        max_amount = max(case.amounts)
        if max_amount >= LARGE_AMOUNT_THRESHOLD:
            matched.append((case, max_amount))

    if not matched:
        return None

    matched.sort(key=lambda item: item[1], reverse=True)
    examples = [
        {
            'case_id': case.case_id,
            'case_number': case.case_number or case.case_id,
            'card_url': case.card_url,
            'max_amount': amount,
        }
        for case, amount in matched[:MAX_EXAMPLES]
    ]

    max_amount_overall = matched[0][1]
    return _make_signal(
        code='kad_arbitr_large_claim_amounts',
        details={
            'threshold': LARGE_AMOUNT_THRESHOLD,
            'matches_count': len(matched),
            'max_amount_overall': max_amount_overall,
            'examples': examples,
        },
    )


def _in_window(
    case: KadArbitrEnrichedCase,
    *,
    now: date,
    months: int,
) -> bool:
    if case.start_date is None:
        return False
    cutoff = now - timedelta(days=30 * months)
    return case.start_date >= cutoff


def _collect_examples(
    cases: list[KadArbitrEnrichedCase],
) -> list[dict[str, str | None]]:
    examples: list[dict[str, str | None]] = []
    for case in cases[:MAX_EXAMPLES]:
        examples.append(
            {
                'case_number': case.case_number or case.case_id,
                'card_url': case.card_url,
            }
        )
    return examples
