"""Порт клиента kad.arbitr.ru."""

from __future__ import annotations

from typing import Protocol

from sources.kad_arbitr.models import (
    KadArbitrSearchPayload,
    KadArbitrSearchResponse,
)


class KadArbitrClientPort(Protocol):
    """Контракт клиента kad.arbitr.ru."""

    async def search_instances(
        self,
        *,
        payload: KadArbitrSearchPayload,
    ) -> KadArbitrSearchResponse:
        """Асинхронно выполнить поиск дел."""
