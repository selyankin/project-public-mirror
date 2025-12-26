"""Нормализованное объявление."""

from __future__ import annotations

from dataclasses import dataclass

from sources.domain.value_objects import ListingId, ListingUrl


@dataclass(slots=True)
class ListingNormalized:
    """Результат нормализации объявления."""

    source: str
    url: ListingUrl
    listing_id: ListingId
    title: str | None = None
    address_text: str | None = None
    price: int | None = None
    coords_lat: float | None = None
    coords_lon: float | None = None
    area_total: float | None = None
    floors_total: int | None = None
