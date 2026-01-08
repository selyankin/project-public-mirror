"""Порт клиента GIS ЖКХ."""

from __future__ import annotations

from typing import Protocol

from sources.gis_gkh.models import GisGkhHouseNormalized


class GisGkhClientPort(Protocol):
    """Контракт клиента GIS ЖКХ."""

    async def search_by_cadnum(
        self,
        *,
        cadnum: str,
        region_code: str,
    ) -> list[GisGkhHouseNormalized]:
        """Асинхронно найти дома по кадастру и региону."""
