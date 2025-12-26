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
