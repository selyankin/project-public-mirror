"""Проверки value-объектов объявлений."""

import pytest

from sources.domain.value_objects import ListingId, ListingUrl


def test_listing_url_accepts_valid_http() -> None:
    """Допускаем корректный http/https URL."""

    url = ListingUrl('https://example.com/listing/1')
    assert str(url) == 'https://example.com/listing/1'


@pytest.mark.parametrize('value', ['', 'ftp://bad', 'http://'])
def test_listing_url_invalid(value: str) -> None:
    """Любые неподдерживаемые схемы отклоняются."""

    with pytest.raises(ValueError):
        ListingUrl(value)


@pytest.mark.parametrize('value', ['', '   ', 'abc def'])
def test_listing_id_invalid(value: str) -> None:
    """Идентификатор не может быть пустым или содержать пробелы."""

    with pytest.raises(ValueError):
        ListingId(value)
