"""Порт поставщиков данных объявлений."""

from __future__ import annotations

from typing import Protocol

from sources.domain.entities import ListingNormalized, ListingSnapshotRaw
from sources.domain.value_objects import ListingUrl


class ListingProviderPort(Protocol):
    """Интерфейс источника объявлений."""

    def is_supported(self, url: ListingUrl) -> bool:
        """Проверить, умеет ли провайдер работать с URL."""

        raise NotImplementedError

    def fetch_snapshot(self, url: ListingUrl) -> ListingSnapshotRaw:
        """Загрузить RAW HTML объявления."""

        raise NotImplementedError

    def normalize(self, snapshot: ListingSnapshotRaw) -> ListingNormalized:
        """Нормализовать данные объявления."""

        raise NotImplementedError
