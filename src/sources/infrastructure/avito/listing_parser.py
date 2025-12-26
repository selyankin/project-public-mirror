"""Парсер Avito preloadedState в ListingNormalized."""

from __future__ import annotations

from collections.abc import Iterable
from typing import Any

from sources.domain.entities import ListingNormalized
from sources.domain.exceptions import ListingParseError
from sources.domain.services import (
    parse_area_total,
    parse_floors_total,
)
from sources.domain.value_objects import ListingId, ListingUrl


def parse_avito_listing(
    *,
    url: ListingUrl,
    preloaded_state: dict[str, object],
) -> ListingNormalized:
    """Преобразовать preloadedState в ListingNormalized."""

    listing_id_raw = _find_value(preloaded_state, ('id', 'listingId', 'itemId'))
    if listing_id_raw is None:
        raise ListingParseError('listing_id is missing')

    listing_id = ListingId(str(listing_id_raw))
    title_raw = _find_value(preloaded_state, ('title',))
    title = str(title_raw) if title_raw is not None else None

    address_raw = _find_value(
        preloaded_state,
        ('fullAddress', 'address', 'locationName'),
    )
    address = str(address_raw) if address_raw is not None else None

    price_raw = _find_value(
        preloaded_state,
        ('price', 'priceValue', 'amount'),
    )
    price = _normalize_int(price_raw)

    coords = _find_value(preloaded_state, ('coordinates',)) or {}
    lat = _as_float(
        _find_value(coords, ('latitude', 'lat')),
    )
    lon = _as_float(
        _find_value(coords, ('longitude', 'lon')),
    )

    area_total = parse_area_total(title) if title else None
    floors_total = parse_floors_total(title) if title else None

    return ListingNormalized(
        source='avito',
        url=url,
        listing_id=listing_id,
        title=title,
        address_text=address,
        price=price,
        coords_lat=lat,
        coords_lon=lon,
        area_total=area_total,
        floors_total=floors_total,
    )


def _find_value(
    data: Any,
    keys: Iterable[str],
    *,
    max_depth: int = 6,
) -> Any:
    """Найти первое попавшееся значение по списку ключей."""

    if max_depth < 0:
        return None

    if isinstance(data, dict):
        for key in keys:
            if key in data:
                return data[key]

        for value in data.values():
            found = _find_value(value, keys, max_depth=max_depth - 1)
            if found is not None:
                return found

    elif isinstance(data, list):
        for item in data:
            found = _find_value(item, keys, max_depth=max_depth - 1)
            if found is not None:
                return found

    return None


def _normalize_int(value: Any) -> int | None:
    """Преобразовать значение в целое число."""

    if isinstance(value, int):
        return value

    if isinstance(value, float):
        return int(value)

    if isinstance(value, str):
        digits = ''.join(ch for ch in value if ch.isdigit())
        if digits:
            try:
                return int(digits)
            except ValueError:
                return None

    if isinstance(value, dict):
        # некоторые узлы могут хранить значение под ключом 'value'
        nested = value.get('value')
        if nested is not None and nested is not value:
            return _normalize_int(nested)

    return None


def _as_float(value: Any) -> float | None:
    """Безопасное приведение к float."""

    if isinstance(value, int | float):
        return float(value)

    if isinstance(value, str):
        try:
            return float(value.replace(',', '.'))
        except ValueError:
            return None

    return None
