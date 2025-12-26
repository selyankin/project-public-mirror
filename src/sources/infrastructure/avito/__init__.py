"""Инфраструктура интеграции с Avito."""

from sources.infrastructure.avito.listing_parser import parse_avito_listing
from sources.infrastructure.avito.preloaded_state import (
    extract_preloaded_state_json,
)
from sources.infrastructure.avito.provider import AvitoListingProvider

__all__ = [
    'extract_preloaded_state_json',
    'parse_avito_listing',
    'AvitoListingProvider',
]
