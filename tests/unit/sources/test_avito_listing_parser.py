"""Проверки парсинга Avito preloadedState."""

import pytest

from sources.domain.exceptions import ListingParseError
from sources.domain.value_objects import ListingUrl
from sources.infrastructure.avito import parse_avito_listing


def test_parse_avito_listing_populates_fields() -> None:
    """Парсер возвращает заполненный ListingNormalized."""

    url = ListingUrl('https://www.avito.ru/item/123')
    preloaded = {
        'data': {
            'item': {
                'id': 'A-123',
                'title': 'Квартира 42,5 м², 5/9 эт.',
                'fullAddress': 'Москва, ул. Тверская',
                'price': {'value': '2 500 000 ₽'},
                'coordinates': {'latitude': 55.75, 'longitude': '37.61'},
            },
        },
    }

    listing = parse_avito_listing(url=url, preloaded_state=preloaded)

    assert listing.listing_id.value == 'A-123'
    assert listing.source == 'avito'
    assert listing.title == 'Квартира 42,5 м², 5/9 эт.'
    assert listing.address_text == 'Москва, ул. Тверская'
    assert listing.price == 2500000
    assert listing.coords_lat == 55.75
    assert listing.coords_lon == 37.61
    assert listing.area_total == 42.5
    assert listing.floors_total == 9


def test_parse_avito_listing_missing_id_raises() -> None:
    """Отсутствие id вызывает ListingParseError."""

    url = ListingUrl('https://www.avito.ru/item/456')
    preloaded = {'data': {'item': {'title': 'Без ID'}}}

    with pytest.raises(ListingParseError):
        parse_avito_listing(url=url, preloaded_state=preloaded)


def test_parse_prefers_primary_paths_over_nested_noise() -> None:
    """Основные пути берут нужные значения несмотря на шум."""

    url = ListingUrl('https://www.avito.ru/item/789')
    preloaded = {
        'tracking': {
            'id': 'noise',
            'price': 0,
        },
        'data': {
            'item': {
                'id': 'PRIMARY-789',
                'title': 'Дом 100 м²',
                'fullAddress': 'Санкт-Петербург, ул. Пушкина',
                'price': {'value': '3 000 000 ₽'},
                'coordinates': {'latitude': 60.0, 'longitude': 30.0},
            },
        },
    }

    listing = parse_avito_listing(url=url, preloaded_state=preloaded)

    assert listing.listing_id.value == 'PRIMARY-789'
    assert listing.price == 3_000_000
    assert listing.coords_lat == 60.0
    assert listing.coords_lon == 30.0


def test_find_value_limits_nodes_and_returns_none():
    """Большие структуры не должны вызывать переполнения."""

    big = {'level': []}
    current = big['level']
    for _ in range(2000):
        node = {'next': []}
        current.append(node)
        current = node['next']
    url = ListingUrl('https://www.avito.ru/item/void')
    with pytest.raises(ListingParseError):
        parse_avito_listing(
            url=url,
            preloaded_state={'tracking': big},
        )
