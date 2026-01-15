"""Проверка извлечения исхода из текста PDF."""

from sources.kad_arbitr.pdf.outcome_extractor import extract_outcome_from_text


def test_outcome_extractor_bankruptcy() -> None:
    text = 'Суд признать банкрот должника и открыть конкурсное производство.'

    outcome = extract_outcome_from_text(text=text)

    assert outcome.outcome == 'bankruptcy_bankrupt_declared'
    assert outcome.confidence == 'high'
    assert outcome.matched_phrase is not None
    assert outcome.evidence_snippet is not None
    assert outcome.matched_phrase in outcome.evidence_snippet


def test_outcome_extractor_denied() -> None:
    text = 'В удовлетворении заявленных требований отказать.'

    outcome = extract_outcome_from_text(text=text)

    assert outcome.outcome == 'denied'
    assert outcome.confidence == 'high'
    assert outcome.matched_phrase is not None
    assert outcome.evidence_snippet is not None


def test_outcome_extractor_partial() -> None:
    text = 'Исковые требования удовлетворить частично.'

    outcome = extract_outcome_from_text(text=text)

    assert outcome.outcome == 'partial'
    assert outcome.confidence == 'high'


def test_outcome_extractor_terminated() -> None:
    text = 'Прекратить производство по делу.'

    outcome = extract_outcome_from_text(text=text)

    assert outcome.outcome == 'terminated'
    assert outcome.confidence == 'medium'


def test_outcome_extractor_unknown() -> None:
    outcome = extract_outcome_from_text(text='')

    assert outcome.outcome == 'unknown'
    assert outcome.confidence == 'low'
