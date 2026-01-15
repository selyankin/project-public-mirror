"""Use-case получения карточки дела kad.arbitr.ru."""

from __future__ import annotations

from sources.kad_arbitr.card_parser import parse_case_card_html
from sources.kad_arbitr.models import KadArbitrCaseDetailsNormalized
from sources.kad_arbitr.ports import KadArbitrClientPort


class ResolveKadArbitrCaseDetails:
    """Use-case получения карточки дела."""

    def __init__(
        self,
        *,
        client: KadArbitrClientPort,
        base_url: str = 'https://kad.arbitr.ru',
    ) -> None:
        """Сохранить зависимости use-case."""

        self._client = client
        self._base_url = base_url

    async def execute(self, *, case_id: str) -> KadArbitrCaseDetailsNormalized:
        """Получить и распарсить карточку дела."""

        html = await self._client.get_case_card_html(case_id=case_id)
        return parse_case_card_html(
            case_id=case_id,
            html=html,
            base_url=self._base_url,
        )
