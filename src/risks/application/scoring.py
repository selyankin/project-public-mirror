"""Scoring utilities for RiskCard construction."""

from __future__ import annotations

from src.risks.domain.entities.risk_card import (
    RiskCard,
    RiskSignal,
    level_from_score,
)

Signals = tuple[RiskSignal, ...]


def score_from_signals(signals: Signals) -> int:
    """Compute a 0..100 risk score from signals."""

    if not signals:
        return 0

    total = sum(int(signal.severity) for signal in signals)
    return min(100, total * 10)


def build_summary(signals: Signals) -> str:
    """Build a short summary for the risk card."""

    if not signals:
        return 'No risk signals found'

    return f'Found {len(signals)} risk signals'


def build_risk_card(signals: Signals) -> RiskCard:
    """Build a RiskCard for the given signals."""

    score = score_from_signals(signals)
    level = level_from_score(score)
    summary = build_summary(signals)
    payload = {
        'score': score,
        'level': level.value,
        'summary': summary,
        'signals': list(signals),
    }
    return RiskCard(payload)
