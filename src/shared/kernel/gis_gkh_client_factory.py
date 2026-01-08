"""Фабрика клиентов GIS ЖКХ."""

from __future__ import annotations

from shared.kernel.settings import Settings
from sources.gis_gkh.ports import GisGkhClientPort
from sources.gis_gkh.stub_client import StubGisGkhClient


def build_gis_gkh_client(settings: Settings) -> GisGkhClientPort:
    """Построить клиента GIS ЖКХ в зависимости от настроек."""

    if settings.GIS_GKH_MODE == 'playwright':
        from sources.gis_gkh.playwright_client import PlaywrightGisGkhClient

        return PlaywrightGisGkhClient(
            timeout_seconds=settings.GIS_GKH_TIMEOUT_SECONDS,
            headless=settings.GIS_GKH_HEADLESS,
            ssl_verify=settings.GIS_GKH_SSL_VERIFY,
        )

    return StubGisGkhClient()
