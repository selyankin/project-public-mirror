"""Доменные сущности нормализованного адреса."""

from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime

from shared.domain.value_objects import AddressText


@dataclass(frozen=True, slots=True)
class HouseKey:
    """Стабильный идентификатор дома."""

    value: str

    def __post_init__(self) -> None:
        """Проверить, что ключ не пустой."""

        if not self.value or not self.value.strip():
            raise ValueError('HouseKey не может быть пустым')

    @staticmethod
    def build(
        *,
        fias_houseguid: str | None = None,
        gar_house_id: str | None = None,
        gar_object_id: str | None = None,
    ) -> HouseKey:
        """Создать ключ в порядке приоритетов идентификаторов."""

        if fias_houseguid:
            return HouseKey(fias_houseguid)
        if gar_house_id:
            return HouseKey(gar_house_id)
        if gar_object_id:
            return HouseKey(gar_object_id)
        raise ValueError('Не удалось построить HouseKey')


@dataclass(slots=True)
class AddressNormalized:
    """Нормализованный адрес с идентификаторами ФИАС/ГАР."""

    source: str
    address_text_raw: AddressText
    address_text_normalized: str | None = None
    fias_houseguid: str | None = None
    fias_aoguid: str | None = None
    gar_house_id: str | None = None
    gar_object_id: str | None = None
    postal_code: str | None = None
    oktmo: str | None = None
    okato: str | None = None
    region_code: str | None = None
    cadastral_number: str | None = None
    status: str | None = None
    is_active: bool | None = None
    updated_at: datetime | None = None
    quality: str | None = None
