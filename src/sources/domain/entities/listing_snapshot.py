"""Сырые снимки объявлений."""

from __future__ import annotations

from dataclasses import dataclass
from datetime import UTC, datetime

from sources.domain.value_objects import ListingUrl


@dataclass(slots=True)
class ListingSnapshotRaw:
    """Снимок объявления на этапе загрузки HTML."""

    source: str
    url: ListingUrl
    fetched_at: datetime
    raw_html: str

    def __post_init__(self) -> None:
        """Убедиться, что время UTC-aware."""

        if self.fetched_at.tzinfo is None:
            raise ValueError('fetched_at должен быть с таймзоной UTC')

        if self.fetched_at.tzinfo != UTC:
            raise ValueError('fetched_at должен быть в UTC')
