"""Проверка парсинга DTO Rosreestr."""

from sources.rosreestr.dto import RosreestrApiResponse


def test_rosreestr_dto_from_dict_parses_nested_fields():
    payload = {
        'status': 200,
        'found': True,
        'object': {
            'cadNumber': '77:01:000101:1',
            'cadCost': '10000000',
            'address': {
                'readableAddress': 'г. Москва, ул. Тверская, д. 1',
                'region': 'Москва',
                'city': 'Москва',
                'street': 'Тверская',
                'house': '1',
            },
            'inquiry': {
                'price': '100',
                'balance': '10',
                'credit': '0',
                'speed': 'fast',
                'attempts': '1',
            },
        },
    }
    dto = RosreestrApiResponse.from_dict(payload)
    assert dto.status == 200
    assert dto.found is True
    assert dto.object is not None
    assert dto.object.cadNumber == '77:01:000101:1'
    assert dto.object.address is not None
    assert dto.object.address.readableAddress == (
        'г. Москва, ул. Тверская, д. 1'
    )
    assert dto.object.inquiry is not None
    assert dto.object.inquiry.balance == '10'
