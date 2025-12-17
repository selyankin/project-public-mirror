"""Тесты DTO для ФИАС."""

from uuid import UUID, uuid4

from checks.infrastructure.fias.dto import FiasSearchAddressItemResponse


def test_search_address_item_response_parses_full_payload() -> None:
    """Проверяет, что DTO принимает полный JSON."""

    object_guid = uuid4()
    successor_guid = uuid4()
    hierarchy_guid = uuid4()
    sample = {
        'object_id': 1,
        'object_level_id': 1,
        'operation_type_id': 1,
        'object_guid': str(object_guid),
        'address_type': 1,
        'full_name': 'г Москва',
        'region_code': 77,
        'is_active': True,
        'path': '/77/7800000000000',
        'address_details': {
            'postal_code': '101000',
            'ifns_ul': '7700',
            'ifns_fl': '7701',
            'ifns_tul': '7702',
            'ifns_tfl': '7703',
            'okato': '45000000000',
            'oktmo': '45000000',
            'kladr_code': '7700000000000',
            'cadastral_number': '77:00:0000000:0',
            'apart_building': '1',
            'remove_cadastr': '0',
            'oktmo_budget': '45000000',
            'is_adm_capital': '1',
            'is_mun_capital': '1',
        },
        'successor_ref': {
            'object_id': 2,
            'object_guid': str(successor_guid),
        },
        'hierarchy': [
            {
                'object_id': 3,
                'object_level_id': 3,
                'object_guid': str(hierarchy_guid),
                'full_name': 'г Москва',
                'full_name_short': 'Москва',
                'kladr_code': '7700000000000',
                'object_type': 'city',
                'hierarchy_place': 1,
                'hist_names': [
                    {
                        'name': 'Москва',
                        'short_type': 'г',
                    },
                ],
            },
        ],
        'federal_district': {
            'id': 1,
            'full_name': 'Центральный',
            'short_name': 'ЦФО',
            'center_id': 77,
        },
        'hierarchy_place': 10,
    }

    model = FiasSearchAddressItemResponse.model_validate(sample)

    assert isinstance(model.object_guid, UUID)
    assert model.address_details is not None
    assert model.address_details.kladr_code == '7700000000000'
    assert model.successor_ref is not None
    assert isinstance(model.successor_ref.object_guid, UUID)
    assert model.hierarchy is not None
    assert model.hierarchy[0].hist_names is not None
    assert model.hierarchy[0].hist_names[0].name == 'Москва'
    assert model.federal_district is not None
    assert model.federal_district.short_name == 'ЦФО'
