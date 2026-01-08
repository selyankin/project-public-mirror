"""Use-case поиска дома GIS ЖКХ по кадастровому номеру."""

from __future__ import annotations

from dataclasses import dataclass

from sources.gis_gkh.models import GisGkhHouseNormalized
from sources.gis_gkh.ports import GisGkhClientPort


@dataclass(slots=True)
class ResolveGisGkhHouseByCadastralUseCase:
    """Получить дом из GIS ЖКХ по кадастровому номеру."""

    client: GisGkhClientPort

    async def execute(
        self,
        *,
        cadastral_number: str,
        region_code: str,
    ) -> GisGkhHouseNormalized | None:
        """Вернуть первый найденный дом или None."""

        results = await self.client.search_by_cadnum(
            cadnum=cadastral_number,
            region_code=region_code,
        )
        return results[0] if results else None
