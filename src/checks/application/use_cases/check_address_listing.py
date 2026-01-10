"""Вспомогательные функции для обработки листинга."""

from __future__ import annotations

import asyncio
import logging
from typing import Any

from checks.domain.helpers.address_heuristics import is_address_like
from checks.domain.value_objects.url import UrlRaw
from sources.domain.entities import ListingNormalized
from sources.domain.exceptions import (
    ListingFetchError,
    ListingNotSupportedError,
    ListingParseError,
)

logger = logging.getLogger(__name__)


async def try_resolve_listing(
    *,
    listing_resolver_uc: Any,
    url: UrlRaw,
) -> tuple[tuple[str, dict[str, Any]] | None, str | None]:
    """Попробовать извлечь адрес из листинга."""

    try:
        listing = await asyncio.to_thread(
            listing_resolver_uc.execute,
            url.value,
        )
    except ListingNotSupportedError as exc:
        logger.info('listing_not_supported url=%s error=%s', url.value, exc)
        return None, 'ListingNotSupportedError'
    except (ListingFetchError, ListingParseError) as exc:
        logger.info(
            'listing_resolver_failed url=%s error=%s',
            url.value,
            exc,
        )
        return None, exc.__class__.__name__
    except Exception as exc:  # pragma: no cover
        logger.warning(
            'listing_resolver_unexpected_error url=%s error=%s',
            url.value,
            exc,
        )
        return None, 'UnexpectedError'

    if listing.address_text and is_address_like(listing.address_text):
        payload = listing_to_payload(listing)
        return (listing.address_text, payload), None

    return None, None


def listing_to_payload(listing: ListingNormalized) -> dict[str, Any]:
    """Сериализовать листинг для хранения."""

    return {
        'source': listing.source,
        'url': listing.url.value,
        'listing_id': listing.listing_id.value,
        'title': listing.title,
        'address_text': listing.address_text,
        'price': listing.price,
        'coords': {
            'lat': listing.coords_lat,
            'lon': listing.coords_lon,
        },
        'area_total': listing.area_total,
        'floors_total': listing.floors_total,
    }
