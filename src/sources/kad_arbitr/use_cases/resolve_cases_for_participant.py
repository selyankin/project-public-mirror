"""Use-case поиска дел для участника kad.arbitr.ru."""

from __future__ import annotations

from dataclasses import dataclass

from sources.kad_arbitr.mapper import normalize_cases
from sources.kad_arbitr.models import (
    KadArbitrCaseNormalized,
    KadArbitrSearchPayload,
    KadArbitrSideFilter,
)
from sources.kad_arbitr.ports import KadArbitrClientPort


@dataclass(slots=True)
class ResolveKadArbitrCasesResult:
    """Результат разрешения дел по участнику."""

    cases: list[KadArbitrCaseNormalized]
    total: int


@dataclass(slots=True)
class ResolveKadArbitrCasesForParticipant:
    """Use-case разрешения дел по участнику."""

    client: KadArbitrClientPort
    base_url: str = 'https://kad.arbitr.ru'

    async def execute(
        self,
        *,
        participant: str,
        participant_type: int | None = None,
        max_pages: int = 3,
    ) -> ResolveKadArbitrCasesResult:
        """Выполнить поиск дел по участнику."""

        payload = KadArbitrSearchPayload(
            page=1,
            count=25,
            sides=[
                KadArbitrSideFilter(
                    name=participant,
                    type=participant_type,
                    exact_match=False,
                )
            ],
        )
        raw_items = []
        total = 0
        pages = 1
        for page in range(1, max_pages + 1):
            payload.page = page
            response = await self.client.search_instances(payload=payload)
            if page == 1:
                total = response.total
                pages = response.pages
            raw_items.extend(response.items)
            if page >= pages:
                break

        cases = normalize_cases(raw_cases=raw_items, base_url=self.base_url)
        return ResolveKadArbitrCasesResult(
            cases=cases,
            total=total,
        )
