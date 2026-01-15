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
        case_cards_by_id: dict[str, str] | None = None,
        case_acts_cards_by_id: dict[str, str] | None = None,
    ) -> None:
        """Сохранить ответ заглушки."""

        self._response = response
        self._case_cards_by_id = case_cards_by_id or {}
        self._case_acts_cards_by_id = case_acts_cards_by_id or {}

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

    async def get_case_card_html(self, *, case_id: str) -> str:
        """Вернуть HTML карточки дела из заглушки."""

        html = self._case_cards_by_id.get(case_id)
        if html is not None:
            return html

        return '<html><body></body></html>'

    async def get_case_acts_html(self, *, case_id: str) -> str:
        """Вернуть HTML актов дела из заглушки."""

        html = self._case_acts_cards_by_id.get(case_id)
        if html is not None:
            return html

        return '<html><body></body></html>'
