"""Сигналы по данным kad.arbitr.ru."""

from __future__ import annotations

from datetime import date, timedelta

from risks.domain.constants.enums.risk import SignalSeverity
from risks.domain.entities.risk_card import RiskSignal
from risks.domain.signals_catalog import get_signal_definition
from sources.kad_arbitr.models import (
    KadArbitrCaseNormalized,
    KadArbitrEnrichedCase,
    is_bankruptcy_outcome,
    is_negative_outcome_for_defendant,
    is_negative_outcome_for_plaintiff,
)


def build_kad_arbitr_signals(
    *,
    cases: list[KadArbitrCaseNormalized],
    now: date | None = None,
) -> list[RiskSignal]:
    """Собрать сигналы по делам kad.arbitr.ru."""

    if not cases:
        return [
            _make_signal(
                code='kad_arbitr_no_cases_found',
                severity=SignalSeverity.info,
                details={'total': 0},
            )
        ]

    signals: list[RiskSignal] = []
    signals.extend(_build_bankruptcy_signals(cases))
    signals.extend(_build_many_cases_signals(cases, now))
    signals.extend(_build_mostly_defendant_signals(cases))
    return signals


def build_kad_arbitr_outcome_signals(
    *,
    cases: list[KadArbitrEnrichedCase],
    now: date | None = None,
) -> list[RiskSignal]:
    """Собрать сигналы по исходам дел kad.arbitr.ru."""

    if not cases:
        return []

    current = now or date.today()
    cutoff = current - timedelta(days=730)
    window_cases = [
        case for case in cases if case.start_date and case.start_date >= cutoff
    ]
    considered = window_cases or cases
    losses = _count_losses(considered)
    losses_defendant = _count_losses_as_defendant(considered)
    unknown_count = len(
        [case for case in considered if case.outcome == 'unknown']
    )

    signals: list[RiskSignal] = []
    if any(is_bankruptcy_outcome(case.outcome) for case in considered):
        signals.append(
            _make_signal(
                code='kad_arbitr_bankruptcy_procedure',
                severity=SignalSeverity.high,
                details=_details_payload(
                    considered=considered,
                    losses=losses,
                    unknown_count=unknown_count,
                    cutoff=cutoff,
                ),
            )
        )

    if losses >= 1:
        signals.append(
            _make_signal(
                code='kad_arbitr_losses_last_24m',
                severity=SignalSeverity.high,
                details=_details_payload(
                    considered=considered,
                    losses=losses,
                    unknown_count=unknown_count,
                    cutoff=cutoff,
                ),
            )
        )

    if losses_defendant >= 3:
        signals.append(
            _make_signal(
                code='kad_arbitr_many_loses_as_defendant',
                severity=SignalSeverity.high,
                details=_details_payload(
                    considered=considered,
                    losses=losses_defendant,
                    unknown_count=unknown_count,
                    cutoff=cutoff,
                ),
            )
        )

    if len(considered) >= 5:
        ratio = unknown_count / len(considered)
        if ratio >= 0.6:
            signals.append(
                _make_signal(
                    code='kad_arbitr_outcome_unknown_many',
                    severity=SignalSeverity.info,
                    details=_details_payload(
                        considered=considered,
                        losses=losses,
                        unknown_count=unknown_count,
                        cutoff=cutoff,
                    ),
                )
            )

    return signals


def _build_bankruptcy_signals(
    cases: list[KadArbitrCaseNormalized],
) -> list[RiskSignal]:
    for case in cases:
        case_type = (case.case_type or '').lower()
        if 'банкрот' in case_type:
            return [
                _make_signal(
                    code='kad_arbitr_has_bankruptcy_cases',
                    severity=SignalSeverity.high,
                    details={'case_id': case.case_id},
                )
            ]
    return []


def _build_many_cases_signals(
    cases: list[KadArbitrCaseNormalized],
    now: date | None,
) -> list[RiskSignal]:
    current = now or date.today()
    cutoff = current - timedelta(days=365)
    recent = [
        case for case in cases if case.start_date and case.start_date >= cutoff
    ]
    count = len(recent)
    if count < 10:
        return []

    severity = SignalSeverity.high if count >= 25 else SignalSeverity.medium
    return [
        _make_signal(
            code='kad_arbitr_many_cases_last_12m',
            severity=severity,
            details={
                'count': count,
                'cutoff': cutoff.isoformat(),
            },
        )
    ]


def _build_mostly_defendant_signals(
    cases: list[KadArbitrCaseNormalized],
) -> list[RiskSignal]:
    if len(cases) < 5:
        return []

    defendant_cases = [
        case for case in cases if case.participant_role == 'defendant'
    ]
    ratio = len(defendant_cases) / len(cases)
    if ratio < 0.7:
        return []

    return [
        _make_signal(
            code='kad_arbitr_mostly_defendant',
            severity=SignalSeverity.medium,
            details={
                'ratio': ratio,
                'total': len(cases),
            },
        )
    ]


def _count_losses(cases: list[KadArbitrEnrichedCase]) -> int:
    losses = 0
    for case in cases:
        if (
            case.target_role == 'defendant'
            and is_negative_outcome_for_defendant(case.outcome)
        ) or (
            case.target_role == 'plaintiff'
            and is_negative_outcome_for_plaintiff(case.outcome)
        ):
            losses += 1

    return losses


def _count_losses_as_defendant(
    cases: list[KadArbitrEnrichedCase],
) -> int:
    losses = 0
    for case in cases:
        if (
            case.target_role == 'defendant'
            and is_negative_outcome_for_defendant(case.outcome)
        ):
            losses += 1

    return losses


def _details_payload(
    *,
    considered: list[KadArbitrEnrichedCase],
    losses: int,
    unknown_count: int,
    cutoff: date,
) -> dict[str, object]:

    return {
        'total_considered': len(considered),
        'losses_count': losses,
        'unknown_count': unknown_count,
        'window_months': 24,
        'max_cases': len(considered),
        'cutoff': cutoff.isoformat(),
        'examples': _sample_cases(considered),
    }


def _sample_cases(
    cases: list[KadArbitrEnrichedCase],
) -> list[dict[str, str]]:
    samples = []
    for case in cases[:3]:
        samples.append(
            {
                'case_id': case.case_id,
                'case_number': case.case_number or case.case_id,
            }
        )

    return samples


def _make_signal(
    *,
    code: str,
    severity: SignalSeverity,
    details: dict[str, object],
) -> RiskSignal:
    definition = get_signal_definition(code)
    return RiskSignal(
        {
            'code': definition.code,
            'title': definition.title,
            'description': definition.description,
            'severity': int(severity),
            'evidence_refs': [],
            'details': details,
        }
    )
