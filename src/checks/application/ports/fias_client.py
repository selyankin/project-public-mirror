"""Порт клиента ФИАС."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Protocol


@dataclass(frozen=True, slots=True)
class NormalizedAddress:
    """Нормализованный адрес, полученный из ФИАС."""

    source_query: str
    normalized: str
    fias_id: str | None
    confidence: float | None
    raw: dict


class FiasClient(Protocol):
    """Контракт клиента ФИАС."""

    async def normalize_address(self, query: str) -> NormalizedAddress | None:
        """Вернуть нормализованный адрес или None при неудаче."""
