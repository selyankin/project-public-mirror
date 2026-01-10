"""Сигналы по данным kad.arbitr.ru."""

from __future__ import annotations

from datetime import date, timedelta

from risks.domain.constants.enums.risk import SignalSeverity
from risks.domain.entities.risk_card import RiskSignal
from risks.domain.signals_catalog import get_signal_definition
from sources.kad_arbitr.models import KadArbitrCaseNormalized


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
