from src.risks.application.scoring import (
    build_risk_card,
    build_summary,
    score_from_signals,
)
from src.risks.domain.entities.risk_card import RiskSignal


def signal(severity, code_prefix='SIG'):
    return RiskSignal(
        {
            'code': f'{code_prefix}-{severity}',
            'title': 'Signal',
            'description': 'Desc',
            'severity': severity,
        },
    )


def test_score_no_signals():
    signals = ()
    assert score_from_signals(signals) == 0
    assert build_summary(signals) == 'No risk signals found'


def test_score_single_critical_signal():
    signals = (signal('critical'),)
    assert score_from_signals(signals) == 50


def test_score_multiple_signals_additive():
    signals = (signal(1), signal(2), signal(3))
    assert score_from_signals(signals) == 60


def test_score_cap_at_100():
    signals = tuple(signal('critical', code_prefix=str(i)) for i in range(11))
    assert score_from_signals(signals) == 100


def test_build_risk_card_returns_consistent_level():
    signals = (signal('critical'),)
    card = build_risk_card(signals)
    assert card.score == 50
    assert card.level.value == 'medium'
    assert card.summary == 'Found 1 risk signals'
    assert len(card.signals) == 1
