"""Помощники для извлечения адреса из URL."""

from __future__ import annotations

from urllib.parse import parse_qs, urlparse

from src.checks.domain.value_objects.url import UrlRaw


def extract_address_from_url(url: UrlRaw) -> str | None:
    """Извлечь строку адреса из параметров URL."""

    parsed = urlparse(url.value)
    params = parse_qs(parsed.query)

    for key in ('address', 'q', 'query'):
        values = params.get(key)
        if not values:
            continue

        candidate = values[0].strip()
        if candidate:
            return candidate

    return None


def is_supported_url(url: UrlRaw) -> bool:
    """Проверить, можно ли извлечь адрес из URL."""

    return extract_address_from_url(url) is not None
