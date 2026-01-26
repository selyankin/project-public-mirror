"""Проверка impact для исходов kad.arbitr.ru."""

from sources.kad_arbitr.models import evaluate_outcome_impact


def test_impact_defendant_negative() -> None:
    impact, confidence = evaluate_outcome_impact(
        outcome='satisfied',
        role_group='defendant_like',
    )

    assert impact == 'negative'
    assert confidence == 'high'


def test_impact_defendant_positive() -> None:
    impact, confidence = evaluate_outcome_impact(
        outcome='denied',
        role_group='defendant_like',
    )

    assert impact == 'positive'
    assert confidence == 'high'


def test_impact_plaintiff_negative() -> None:
    impact, confidence = evaluate_outcome_impact(
        outcome='denied',
        role_group='plaintiff_like',
    )

    assert impact == 'negative'
    assert confidence == 'high'


def test_impact_plaintiff_positive() -> None:
    impact, confidence = evaluate_outcome_impact(
        outcome='satisfied',
        role_group='plaintiff_like',
    )

    assert impact == 'positive'
    assert confidence == 'high'


def test_impact_bankruptcy_defendant() -> None:
    impact, confidence = evaluate_outcome_impact(
        outcome='bankruptcy_competition',
        role_group='defendant_like',
    )

    assert impact == 'negative'
    assert confidence == 'high'


def test_impact_unknown() -> None:
    impact, confidence = evaluate_outcome_impact(
        outcome='unknown',
        role_group='unknown',
    )

    assert impact == 'unknown'
    assert confidence == 'low'
