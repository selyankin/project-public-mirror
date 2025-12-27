"""Маппинг DTO ФИАС в доменную сущность нормализованного адреса."""

from __future__ import annotations

from checks.application.ports.fias_client import NormalizedAddress as FiasDTO
from shared.domain.entities import AddressNormalized
from shared.domain.value_objects import AddressText


def map_fias_normalized_address(
    *,
    raw: AddressText,
    dto: FiasDTO,
) -> AddressNormalized:
    """Преобразовать DTO ФИАС в доменную модель."""

    quality = _map_quality(dto.confidence)
    return AddressNormalized(
        source='fias',
        address_text_raw=raw,
        address_text_normalized=dto.normalized,
        fias_houseguid=dto.fias_houseguid,
        fias_aoguid=dto.fias_aoguid,
        gar_house_id=dto.gar_house_id,
        gar_object_id=dto.gar_object_id,
        postal_code=dto.postal_code,
        oktmo=dto.oktmo,
        okato=dto.okato,
        region_code=dto.region_code,
        cadastral_number=dto.cadastral_number,
        status=dto.status,
        is_active=dto.is_active,
        updated_at=dto.updated_at,
        quality=quality,
    )


def _map_quality(confidence: float | None) -> str | None:
    """Сконвертировать confidence в текстовую оценку."""

    if confidence is None:
        return None
    if confidence >= 0.9:
        return 'exact'
    if confidence >= 0.7:
        return 'high'
    if confidence >= 0.5:
        return 'medium'
    return 'low'
