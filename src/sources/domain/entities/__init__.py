"""Доменные сущности источников."""

from sources.domain.entities.listing import ListingNormalized
from sources.domain.entities.listing_snapshot import ListingSnapshotRaw

__all__ = [
    'ListingNormalized',
    'ListingSnapshotRaw',
]
