"""Проверки парсинга заголовков объявлений."""

import pytest

from sources.domain.services import parse_area_total, parse_floors_total


@pytest.mark.parametrize(
    ('title', 'expected'),
    [
        ('Студия 27 м²', 27.0),
        ('Квартира 42,5 м²', 42.5),
        ('Большая 42.5 м2', 42.5),
        ('Дом 120 кв. м', 120.0),
        ('Комната 17', None),
    ],
)
def test_parse_area_total(title: str, expected: float | None) -> None:
    """Парсер корректно извлекает площадь или возвращает None."""

    assert parse_area_total(title) == expected


@pytest.mark.parametrize(
    ('title', 'expected'),
    [
        ('5/9 эт.', 9),
        ('5 / 9 эт', 9),
        ('12/25 этаж', 25),
        ('этаж 12/25', 25),
        ('Таунхаус 3/3', 3),
        ('Без этажности', None),
    ],
)
def test_parse_floors_total(title: str, expected: int | None) -> None:
    """Парсер извлекает этажность дома."""

    assert parse_floors_total(title) == expected
