"""Проверки преобразования DTO ФИАС в доменные модели."""

from datetime import UTC, datetime

from checks.infrastructure.fias.client import ApiFiasClient


def test_parse_normalized_extracts_extended_fields(monkeypatch):
    """Парсер извлекает дополнительные поля."""

    payload = {
        'full_name': 'г. Москва, ул. Тверская, д. 1',
        'object_guid': 'moscow-fias-id',
        'houseguid': 'house-guid',
        'aoguid': 'ao-guid',
        'gar_house_id': 'gar-house',
        'gar_object_id': 'gar-object',
        'postalcode': '101000',
        'oktmo': '45000000',
        'okato': '45000000000',
        'regioncode': '77',
        'cadnum': '77:01:000101',
        'livestatus': True,
        'updatedate': '2024-05-01T12:34:56+00:00',
        'search_precision': '0.9',
    }

    result = ApiFiasClient._parse_normalized(payload, 'query')
    assert result is not None
    assert result.normalized == payload['full_name']
    assert result.fias_houseguid == 'house-guid'
    assert result.fias_aoguid == 'ao-guid'
    assert result.gar_house_id == 'gar-house'
    assert result.gar_object_id == 'gar-object'
    assert result.postal_code == '101000'
    assert result.oktmo == '45000000'
    assert result.okato == '45000000000'
    assert result.region_code == '77'
    assert result.cadastral_number == '77:01:000101'
    assert result.is_active is True
    assert result.updated_at == datetime(2024, 5, 1, 12, 34, 56, tzinfo=UTC)


def test_parse_normalized_missing_optional_fields():
    """Если поля отсутствуют, возвращаются None."""

    payload = {
        'full_name': 'г. Казань, ул. Баумана, д. 3',
        'object_guid': 'kzn-fias',
    }
    result = ApiFiasClient._parse_normalized(payload, 'query')
    assert result is not None
    assert result.fias_houseguid == 'kzn-fias'
    assert result.postal_code is None
    assert result.is_active is None
    assert result.updated_at is None
