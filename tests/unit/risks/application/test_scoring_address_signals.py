"""Проверки скоринга для сигналов уверенности адреса."""

from risks.application.scoring import build_risk_card
from risks.domain.entities.risk_card import RiskSignal
from risks.domain.signals_catalog import get_signal_definition


def _signal(code: str) -> RiskSignal:
    definition = get_signal_definition(code)
    return RiskSignal(
        {
            'code': definition.code,
            'title': definition.title,
            'description': definition.description,
            'severity': int(definition.severity),
            'evidence_refs': (),
        },
    )


def test_low_confidence_signal_affects_score() -> None:
    """Сигнал низкой уверенности повышает риск."""

    card = build_risk_card((_signal('address_confidence_low'),))

    assert card.score >= 30
    assert card.level.value == 'medium'
