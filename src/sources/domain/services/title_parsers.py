"""Парсеры характеристик объявления из заголовка."""

from __future__ import annotations

from sources.domain.constants.title_parser import AREA_PATTERN, FLOORS_PATTERN


def parse_area_total(title: str) -> float | None:
    """Извлечь общую площадь из заголовка."""

    if not title:
        return None

    match = AREA_PATTERN.search(title)
    if not match:
        return None

    raw = match.group('value').replace(',', '.')
    try:
        return float(raw)
    except ValueError:
        return None


def parse_floors_total(title: str) -> int | None:
    """Извлечь этажность дома."""

    if not title:
        return None

    match = FLOORS_PATTERN.search(title)
    if not match:
        return None

    try:
        return int(match.group('total'))
    except ValueError:
        return None
