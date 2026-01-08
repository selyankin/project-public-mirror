"""Проверка фабрики клиентов GIS ЖКХ."""

from types import SimpleNamespace

from shared.kernel.gis_gkh_client_factory import build_gis_gkh_client
from sources.gis_gkh.stub_client import StubGisGkhClient


def test_factory_returns_stub_client() -> None:
    settings = SimpleNamespace(
        GIS_GKH_MODE='stub',
        GIS_GKH_TIMEOUT_SECONDS=60,
        GIS_GKH_HEADLESS=True,
        GIS_GKH_SSL_VERIFY=True,
    )
    client = build_gis_gkh_client(settings)
    assert isinstance(client, StubGisGkhClient)


def test_factory_returns_playwright_client() -> None:
    settings = SimpleNamespace(
        GIS_GKH_MODE='playwright',
        GIS_GKH_TIMEOUT_SECONDS=60,
        GIS_GKH_HEADLESS=True,
        GIS_GKH_SSL_VERIFY=True,
    )
    client = build_gis_gkh_client(settings)
    assert client.__class__.__name__ == 'PlaywrightGisGkhClient'
