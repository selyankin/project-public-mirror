import pytest
from risks.domain.constants.enums.risk import SignalSeverity
from risks.domain.entities.risk_card import (
    RiskCard,
    RiskDomainError,
    RiskSignal,
    level_from_score,
)


def card_payload(**overrides):
    payload = {
        'score': 55,
        'level': 'medium',
        'summary': 'Risk summary',
        'signals': [
            {
                'code': 'SIG-1',
                'title': 'Signal',
                'description': 'Description',
                'severity': 'low',
            },
        ],
    }
    payload.update(overrides)
    return payload


def signal_payload(**overrides):
    payload = {
        'code': 'CODE1',
        'title': 'Title',
        'description': 'Description',
        'severity': 'high',
        'evidence_refs': ['doc'],
    }
    payload.update(overrides)
    return payload


def test_level_from_score_boundaries():
    assert level_from_score(0).value == 'low'
    assert level_from_score(29).value == 'low'
    assert level_from_score(30).value == 'medium'
    assert level_from_score(69).value == 'medium'
    assert level_from_score(70).value == 'high'
    assert level_from_score(100).value == 'high'


def test_risk_signal_validates_empty_fields_and_severity():
    with pytest.raises(RiskDomainError):
        RiskSignal(signal_payload(code='  '))

    signal = RiskSignal(signal_payload(severity='CRITICAL'))
    assert signal.severity is SignalSeverity.critical

    signal_int = RiskSignal(signal_payload(severity=4))
    assert signal_int.severity is SignalSeverity.high


def test_risk_card_validates_score_range():
    with pytest.raises(RiskDomainError):
        RiskCard(card_payload(score=101))
    with pytest.raises(RiskDomainError):
        RiskCard(card_payload(score=-1))


def test_risk_card_validates_score_level_alignment():
    with pytest.raises(RiskDomainError):
        RiskCard(card_payload(score=10, level='medium'))


def test_risk_card_accepts_signal_dicts_and_returns_tuple():
    card = RiskCard(card_payload(signals=[signal_payload()]))
    assert isinstance(card.signals, tuple)
    assert all(isinstance(sig, RiskSignal) for sig in card.signals)


def test_risk_card_to_dict_serializes_signals():
    card = RiskCard(card_payload())
    data = card.to_dict()
    assert data['level'] == 'medium'
    assert isinstance(data['signals'][0], dict)
    assert data['signals'][0]['severity'] == int(SignalSeverity.low)
