"""Singleton-контейнер для use-case GIS ЖКХ."""

from __future__ import annotations

from shared.kernel.gis_gkh_client_factory import build_gis_gkh_client
from shared.kernel.settings import Settings
from sources.gis_gkh.use_cases.resolve_house_by_cadastral import (
    ResolveGisGkhHouseByCadastralUseCase,
)

_use_case: ResolveGisGkhHouseByCadastralUseCase | None = None


def get_gis_gkh_resolver_use_case(
    settings: Settings,
) -> ResolveGisGkhHouseByCadastralUseCase:
    """Вернуть singleton use-case разрешения GIS ЖКХ."""

    global _use_case
    if _use_case is None:
        client = build_gis_gkh_client(settings)
        _use_case = ResolveGisGkhHouseByCadastralUseCase(client=client)

    return _use_case


def reset_gis_gkh_resolver_container() -> None:
    """Сбросить singleton (для тестов)."""

    global _use_case
    _use_case = None
