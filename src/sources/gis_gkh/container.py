"""Контейнер use-case GIS ЖКХ."""

from __future__ import annotations

from shared.kernel.gis_gkh_client_factory import build_gis_gkh_client
from shared.kernel.settings import Settings
from sources.gis_gkh.use_cases.resolve_house_by_cadastral import (
    ResolveGisGkhHouseByCadastralUseCase,
)


def build_resolve_house_use_case(
    settings: Settings,
) -> ResolveGisGkhHouseByCadastralUseCase:
    """Построить use-case для запроса домов."""

    client = build_gis_gkh_client(settings)
    return ResolveGisGkhHouseByCadastralUseCase(client=client)
