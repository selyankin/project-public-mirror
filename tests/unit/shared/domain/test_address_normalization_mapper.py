"""Проверка маппера нормализованного адреса."""

from datetime import UTC, datetime

from checks.application.ports.fias_client import NormalizedAddress as FiasDTO
from shared.domain.services import map_fias_normalized_address
from shared.domain.value_objects import AddressText


def test_map_fias_normalized_address_transfers_fields() -> None:
    """Все поля DTO переносятся в доменную модель."""

    dto = FiasDTO(
        source_query='г. Москва, ул. Тверская, 1',
        normalized='г. Москва, ул. Тверская, д. 1',
        fias_id='fias-1',
        confidence=0.92,
        raw={'full_name': 'г. Москва, ул. Тверская, д. 1'},
        fias_houseguid='house-guid',
        fias_aoguid='ao-guid',
        gar_house_id='gar-house',
        gar_object_id='gar-object',
        postal_code='101000',
        oktmo='45000000',
        okato='45000000000',
        region_code='77',
        cadastral_number='77:01:000101',
        status='active',
        is_active=True,
        updated_at=datetime(2024, 1, 1, tzinfo=UTC),
    )
    raw = AddressText('г. Москва, ул. Тверская, 1')

    mapped = map_fias_normalized_address(raw=raw, dto=dto)

    assert mapped.source == 'fias'
    assert mapped.address_text_raw == raw
    assert mapped.address_text_normalized == dto.normalized
    assert mapped.fias_houseguid == 'house-guid'
    assert mapped.region_code == '77'
    assert mapped.okato == '45000000000'
    assert mapped.quality == 'exact'


def test_map_fias_handles_missing_fields() -> None:
    """Отсутствующие поля маппятся как None."""

    dto = FiasDTO(
        source_query='г. Казань, ул. Баумана, 3',
        normalized='г. Казань, ул. Баумана, д. 3',
        fias_id='kzn-1',
        confidence=0.5,
        raw={},
    )
    raw = AddressText('г. Казань, ул. Баумана, 3')

    mapped = map_fias_normalized_address(raw=raw, dto=dto)

    assert mapped.fias_houseguid is None
    assert mapped.postal_code is None
    assert mapped.quality == 'medium'
