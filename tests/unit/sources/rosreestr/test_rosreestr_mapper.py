"""Проверка маппера нормализованного объекта Росреестра."""

from datetime import date

import pytest

from sources.rosreestr.dto import RosreestrApiResponse
from sources.rosreestr.mapper import map_object_to_normalized


def test_map_object_to_normalized_populates_fields():
    payload = {
        'status': 200,
        'found': True,
        'object': {
            'cadNumber': '77:01:000101:1',
            'objectType': 'building',
            'purpose': 'жилое помещение',
            'status': '1',
            'area': '43.90',
            'level': '16',
            'undergroundFloors': '1',
            'wallMaterial': 'Монолит',
            'commissioningYear': '2011',
            'yearBuild': '2010',
            'cadCost': '1533640.53',
            'cadUnitDate': '06.10.2021',
            'infoUpdate': '05.04.2022',
            'regDate': '22.09.2021',
            'address': {
                'readableAddress': 'г. Москва, ул. Тверская, д. 1',
            },
            'encumbrances': [{'typeDesc': 'ипотека'}],
            'rights': [
                {'rightTypeDesc': 'собственность'},
                {'rightTypeDesc': 'аренда'},
            ],
            'inquiry': {
                'price': '4500',
                'balance': '150.5',
                'speed': '15',
                'attempts': '2',
            },
        },
    }
    response = RosreestrApiResponse.from_dict(payload)
    normalized = map_object_to_normalized(response.object)
    assert normalized is not None
    assert normalized.cad_number == '77:01:000101:1'
    assert normalized.readable_address == ('г. Москва, ул. Тверская, д. 1')
    assert normalized.is_actual is True
    assert normalized.area_total == pytest.approx(43.9)
    assert normalized.level == 16
    assert normalized.underground_floors == 1
    assert normalized.wall_material == 'Монолит'
    assert normalized.year_build == 2010
    assert normalized.cadastral_value == pytest.approx(1533640.53)
    assert normalized.cadastral_value_date == date(2021, 10, 6)
    assert normalized.info_update_date == date(2022, 4, 5)
    assert normalized.reg_date == date(2021, 9, 22)
    assert normalized.encumbrances_count == 1
    assert normalized.rights_count == 2
    assert normalized.inquiry_balance == pytest.approx(150.5)
    assert normalized.inquiry_speed == 15
    assert normalized.inquiry_attempts == 2


def test_map_object_to_normalized_returns_none_when_no_object():
    normalized = map_object_to_normalized(None)
    assert normalized is None
