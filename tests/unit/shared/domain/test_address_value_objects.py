"""Проверки value-объектов адресов."""

import pytest

from shared.domain.entities import HouseKey
from shared.domain.value_objects import AddressText


def test_address_text_trim_and_normalize() -> None:
    """AddressText нормализует пробелы."""

    text = AddressText('  г.  Москва   ул.  Тверская  ')
    assert text.value == 'г. Москва ул. Тверская'


@pytest.mark.parametrize('raw', ['', '   '])
def test_address_text_rejects_empty(raw: str) -> None:
    """Пустой текст адреса не допускается."""

    with pytest.raises(ValueError):
        AddressText(raw)


def test_house_key_build_with_priority() -> None:
    """HouseKey выбирает идентификаторы по приоритету."""

    key = HouseKey.build(
        fias_houseguid='fias-guid',
        gar_house_id='gar-house',
        gar_object_id='gar-object',
    )
    assert key.value == 'fias-guid'

    key = HouseKey.build(
        fias_houseguid=None,
        gar_house_id='gar-house',
        gar_object_id='gar-object',
    )
    assert key.value == 'gar-house'

    key = HouseKey.build(
        fias_houseguid=None,
        gar_house_id=None,
        gar_object_id='gar-object',
    )
    assert key.value == 'gar-object'


def test_house_key_build_requires_any_id() -> None:
    """Если идентификаторы отсутствуют, получаем ошибку."""

    with pytest.raises(ValueError):
        HouseKey.build(
            fias_houseguid=None,
            gar_house_id=None,
            gar_object_id=None,
        )
