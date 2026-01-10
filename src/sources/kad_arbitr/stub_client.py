"""Заглушка клиента kad.arbitr.ru."""

from __future__ import annotations

from sources.kad_arbitr.models import (
    KadArbitrSearchPayload,
    KadArbitrSearchResponse,
)
from sources.kad_arbitr.ports import KadArbitrClientPort


class StubKadArbitrClient(KadArbitrClientPort):
    """Возвращает заранее заданный результат."""

    def __init__(
        self,
        *,
        response: KadArbitrSearchResponse | None = None,
    ) -> None:
        """Сохранить ответ заглушки."""

        self._response = response

    async def search_instances(
        self,
        *,
        payload: KadArbitrSearchPayload,
    ) -> KadArbitrSearchResponse:
        """Вернуть ответ заглушки."""

        if self._response is None:
            return KadArbitrSearchResponse(
                items=[],
                total=0,
                page=payload.page,
                pages=1,
            )

        return self._response
