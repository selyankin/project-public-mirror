"""Use-case получения судебных актов kad.arbitr.ru."""

from __future__ import annotations

from sources.kad_arbitr.acts_parser import parse_case_acts_html
from sources.kad_arbitr.models import KadArbitrCaseActsNormalized
from sources.kad_arbitr.ports import KadArbitrClientPort


class ResolveKadArbitrCaseActs:
    """Use-case получения судебных актов."""

    def __init__(
        self,
        *,
        client: KadArbitrClientPort,
        base_url: str = 'https://kad.arbitr.ru',
    ) -> None:
        """Сохранить зависимости use-case."""

        self._client = client
        self._base_url = base_url

    async def execute(self, *, case_id: str) -> KadArbitrCaseActsNormalized:
        """Получить и распарсить акты по делу."""

        html = await self._client.get_case_acts_html(case_id=case_id)
        return parse_case_acts_html(
            case_id=case_id,
            html=html,
            base_url=self._base_url,
        )
