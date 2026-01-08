"""Заглушка клиента GIS ЖКХ."""

from __future__ import annotations

from sources.gis_gkh.models import GisGkhHouseNormalized
from sources.gis_gkh.ports import GisGkhClientPort


class StubGisGkhClient(GisGkhClientPort):
    """Возвращает заранее заданный результат."""

    def __init__(self, result: GisGkhHouseNormalized | None = None) -> None:
        """Сохранить результат заглушки."""

        self._result = result

    async def search_by_cadnum(
        self,
        *,
        cadnum: str,
        region_code: str,
    ) -> list[GisGkhHouseNormalized]:
        """Вернуть список домов или пустой."""

        if self._result is None:
            return []

        if self._result.cadastral_number != cadnum:
            return []

        return [self._result]
