"""Проверка извлечения исхода из текста PDF."""

from sources.kad_arbitr.pdf.outcome_extractor import extract_outcome_from_text


def _assert_match(outcome, expected: str) -> None:
    assert outcome.outcome == expected
    assert outcome.confidence != 'low'
    assert outcome.matched_rule_id is not None
    assert outcome.matched_pattern is not None
    assert outcome.matched_phrase is not None
    assert outcome.evidence_snippet is not None


def test_outcome_extractor_bankruptcy_declared() -> None:
    text = (
        'Решил: признать банкрот должника. ' 'Ввести конкурсное производство.'
    )

    outcome = extract_outcome_from_text(text=text)

    _assert_match(outcome, 'bankruptcy_bankrupt_declared')


def test_outcome_extractor_bankruptcy_competition() -> None:
    text = 'Постановил: ввести конкурсное производство.'

    outcome = extract_outcome_from_text(text=text)

    _assert_match(outcome, 'bankruptcy_competition')


def test_outcome_extractor_settlement() -> None:
    text = 'Определил: утвердить мировое соглашение сторон.'

    outcome = extract_outcome_from_text(text=text)

    _assert_match(outcome, 'settlement_approved')


def test_outcome_extractor_partial() -> None:
    text = 'Исковые требования удовлетворить частично.'

    outcome = extract_outcome_from_text(text=text)

    _assert_match(outcome, 'partial')


def test_outcome_extractor_satisfied() -> None:
    text = 'Исковые требования удовлетворить.'

    outcome = extract_outcome_from_text(text=text)

    _assert_match(outcome, 'satisfied')


def test_outcome_extractor_denied() -> None:
    text = 'В удовлетворении заявленных требований отказать.'

    outcome = extract_outcome_from_text(text=text)

    _assert_match(outcome, 'denied')


def test_outcome_extractor_terminated() -> None:
    text = 'Прекратить производство по делу.'

    outcome = extract_outcome_from_text(text=text)

    _assert_match(outcome, 'terminated')


def test_outcome_extractor_left_without_review() -> None:
    text = 'Оставить заявление без рассмотрения.'

    outcome = extract_outcome_from_text(text=text)

    _assert_match(outcome, 'left_without_review')


def test_outcome_extractor_appeal_left_unchanged() -> None:
    text = 'Решение суда оставить без изменения.'

    outcome = extract_outcome_from_text(text=text)

    _assert_match(outcome, 'appeal_left_unchanged')


def test_outcome_extractor_appeal_canceled() -> None:
    text = 'Определение суда отменить.'

    outcome = extract_outcome_from_text(text=text)

    _assert_match(outcome, 'appeal_canceled')


def test_outcome_extractor_appeal_changed() -> None:
    text = 'Решение суда изменить.'

    outcome = extract_outcome_from_text(text=text)

    _assert_match(outcome, 'appeal_changed')


def test_outcome_extractor_complaint_left_unsatisfied() -> None:
    text = 'Жалобу оставить без удовлетворения.'

    outcome = extract_outcome_from_text(text=text)

    _assert_match(outcome, 'complaint_left_unsatisfied')


def test_outcome_extractor_negative_pattern() -> None:
    text = 'Истец просил удовлетворить иск.'

    outcome = extract_outcome_from_text(text=text)

    assert outcome.outcome == 'unknown'
    assert outcome.confidence == 'low'
