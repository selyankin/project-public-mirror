"""Проверка извлечения сумм из текста."""

from sources.kad_arbitr.amounts_extractor import extract_amounts


def test_extract_amounts_simple_rubles() -> None:
    text = 'Взыскать 1 234 567 руб. 89 коп.'

    result = extract_amounts(text=text, max_amounts=3)

    assert result.amounts == [1234567]
    assert result.matched_fragments


def test_extract_amounts_decimal_rubles() -> None:
    text = 'Взыскать 12 345,67 ₽.'

    result = extract_amounts(text=text, max_amounts=3)

    assert result.amounts == [12345]


def test_extract_amounts_filters_small_values() -> None:
    text = 'Сумма 999 руб.'

    result = extract_amounts(text=text, max_amounts=3)

    assert result.amounts == []


def test_extract_amounts_sorted_and_limited() -> None:
    text = 'Взыскать 120 000 руб. и штраф 2 000 руб. ' 'Также 3 500 000 руб.'

    result = extract_amounts(text=text, max_amounts=3)

    assert result.amounts == [3500000, 120000, 2000]


def test_extract_amounts_dedupes() -> None:
    text = 'Взыскать 50 000 руб. и снова 50 000 руб.'

    result = extract_amounts(text=text, max_amounts=3)

    assert result.amounts == [50000]
