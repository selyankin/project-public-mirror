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
from sources.infrastructure.avito.constants.parser import (
    ADDRESS_PATHS,
    COORDS_PATHS,
    ID_PATTERN,
    LISTING_ID_PATHS,
    PRICE_PATHS,
    TITLE_PATHS,
)


def parse_avito_listing(
    *,
    url: ListingUrl,
    preloaded_state: dict[str, object],
) -> ListingNormalized:
    """Преобразовать preloadedState в ListingNormalized."""

    listing_id_raw = _get_by_paths(preloaded_state, LISTING_ID_PATHS)
    if listing_id_raw is None:
        listing_id_raw = _find_value(
            preloaded_state,
            ('id', 'listingId', 'itemId'),
            max_nodes=5000,
        )

    listing_id_value = _normalize_listing_id(listing_id_raw)
    if listing_id_value is None:
        raise ListingParseError('listing_id is missing')
    listing_id = ListingId(listing_id_value)

    title_raw = _get_by_paths(preloaded_state, TITLE_PATHS)
    if title_raw is None:
        title_raw = _find_value(preloaded_state, ('title',), max_nodes=5000)
    title = str(title_raw) if title_raw is not None else None

    address_raw = _get_by_paths(preloaded_state, ADDRESS_PATHS)
    if address_raw is None:
        address_raw = _find_value(
            preloaded_state,
            ('fullAddress', 'address', 'locationName'),
            max_nodes=5000,
        )
    address = str(address_raw) if address_raw is not None else None

    price_raw = _get_by_paths(preloaded_state, PRICE_PATHS)
    if price_raw is None:
        price_raw = _find_value(
            preloaded_state,
            ('price', 'priceValue', 'amount'),
            max_nodes=5000,
        )
    price = _normalize_int(price_raw)

    coords = _get_by_paths(preloaded_state, COORDS_PATHS)
    if coords is None:
        coords = _find_value(preloaded_state, ('coordinates',), max_nodes=5000)

    coords = coords or {}
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


def _get_by_paths(
    data: dict[str, Any],
    paths: list[list[str]],
) -> Any:
    """Пройти по набору путей и вернуть первое найденное значение."""

    for path in paths:
        current: Any = data
        matched = True
        for key in path:
            if not isinstance(current, dict):
                matched = False
                break

            if key not in current:
                matched = False
                break

            current = current[key]

        if matched:
            return current

    return None


def _find_value(
    data: Any,
    keys: Iterable[str],
    *,
    max_depth: int = 6,
    max_nodes: int = 5000,
) -> Any:
    """Найти значение по ключам с ограничением глубины и узлов."""

    visited = 0

    def _inner(node: Any, depth: int) -> Any:
        nonlocal visited
        if depth < 0:
            return None

        if visited >= max_nodes:
            return None

        visited += 1
        if isinstance(node, dict):
            for key in keys:
                if key in node:
                    return node[key]

            for value in node.values():
                found = _inner(value, depth - 1)
                if found is not None:
                    return found

        elif isinstance(node, list):
            for item in node:
                found = _inner(item, depth - 1)
                if found is not None:
                    return found

        return None

    return _inner(data, max_depth)


def _normalize_listing_id(value: Any) -> str | None:
    """Проверить и привести listing_id."""

    if isinstance(value, int):
        return str(value) if value > 0 else None
    if isinstance(value, str):
        trimmed = value.strip()
        if not trimmed:
            return None

        if trimmed.isdigit() or ID_PATTERN.match(trimmed):
            return trimmed

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

    if isinstance(value, (int, float)):
        return float(value)

    if isinstance(value, str):
        try:
            return float(value.replace(',', '.'))
        except ValueError:
            return None

    return None
