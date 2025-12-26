"""Утилита извлечения window.__preloadedState__ из HTML."""

from __future__ import annotations

from sources.domain.exceptions import ListingParseError
from sources.infrastructure.avito.constants.preloader import PRELOADED_PATTERN


def extract_preloaded_state_json(html: str) -> str:
    """Вернуть JSON из window.__preloadedState__."""

    match = PRELOADED_PATTERN.search(html)
    if not match:
        raise ListingParseError('preloaded state not found')

    return match.group(1)
