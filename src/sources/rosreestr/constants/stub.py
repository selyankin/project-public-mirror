from sources.rosreestr.dto import RosreestrObjectDto

ROSREESTR_FIXTURE = {
    '77:01:000101:1': RosreestrObjectDto.from_dict(
        {
            'cadNumber': '77:01:000101:1',
            'cadCost': '10000000',
            'infoUpdate': '2024-05-01',
            'address': {
                'readableAddress': 'г. Москва, ул. Тверская, д. 1',
                'region': 'Москва',
                'city': 'Москва',
                'street': 'Тверская',
                'house': '1',
            },
            'inquiry': {
                'price': '100',
                'balance': '0',
                'speed': 'fast',
                'attempts': '1',
            },
        }
    )
}
