"""Проверка классификатора предмета спора."""

from sources.kad_arbitr.claim_classifier import classify_claim


def test_claim_classifier_bankruptcy() -> None:
    text = 'Суд решил: признать банкротом должника.'

    result = classify_claim(text=text)

    assert result.categories == ['bankruptcy']
    assert result.confidence == 'high'
    assert result.matched_keywords


def test_claim_classifier_ddu_penalty() -> None:
    text = (
        'Договор долевого участия по 214-ФЗ. '
        'Просим взыскать неустойку с застройщика.'
    )

    result = classify_claim(text=text)

    assert result.categories == ['ddu_penalty']


def test_claim_classifier_utilities() -> None:
    text = 'Спор с управляющей компанией ЖКХ о взносах.'

    result = classify_claim(text=text)

    assert result.categories == ['utilities_and_management']


def test_claim_classifier_debt_collection() -> None:
    text = 'Взыскать задолженность и проценты по договору.'

    result = classify_claim(text=text)

    assert result.categories == ['debt_collection']


def test_claim_classifier_unknown() -> None:
    text = 'Процессуальные вопросы без явных ключевых слов.'

    result = classify_claim(text=text)

    assert result.categories == ['unknown']
    assert result.confidence == 'low'
    assert result.matched_keywords == []


def test_claim_classifier_multiple_categories() -> None:
    text = 'Аренда и задолженность по договору аренды.'

    result = classify_claim(text=text)

    assert set(result.categories) == {'rent_and_lease', 'debt_collection'}
    assert result.confidence == 'medium'
    assert result.matched_keywords
