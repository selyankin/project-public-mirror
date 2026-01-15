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

    async def get_case_card_html(self, *, case_id: str) -> str:
        """Асинхронно получить HTML карточки дела."""

    async def get_case_acts_html(self, *, case_id: str) -> str:
        """Асинхронно получить HTML со списком актов дела."""
