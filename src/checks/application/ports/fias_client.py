"""Порт клиента ФИАС."""

from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime
from typing import Protocol


@dataclass(frozen=True, slots=True)
class NormalizedAddress:
    """Нормализованный адрес, полученный из ФИАС."""

    source_query: str
    normalized: str
    fias_id: str | None
    confidence: float | None
    raw: dict
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


class FiasClient(Protocol):
    """Контракт клиента ФИАС."""

    async def normalize_address(self, query: str) -> NormalizedAddress | None:
        """Вернуть нормализованный адрес или None при неудаче."""
