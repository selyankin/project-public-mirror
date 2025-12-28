"""Проверка фабрики клиентов Росреестра."""

from types import SimpleNamespace

from shared.kernel.rosreestr_client_factory import build_rosreestr_client
from sources.rosreestr.api_cloud_client import ApiCloudRosreestrClient
from sources.rosreestr.stub_client import StubRosreestrClient


def test_factory_returns_stub_for_stub_mode():
    settings = SimpleNamespace(
        ROSREESTR_MODE='stub',
        ROSREESTR_TOKEN=None,
        ROSREESTR_TIMEOUT_SECONDS=120,
        ROSREESTR_CACHE_MODE='none',
        ROSREESTR_CACHE_TTL_SECONDS=100,
    )
    client = build_rosreestr_client(settings)
    assert isinstance(client, StubRosreestrClient)


def test_factory_returns_api_client_for_api_mode():
    settings = SimpleNamespace(
        ROSREESTR_MODE='api_cloud',
        ROSREESTR_TOKEN='token',
        ROSREESTR_TIMEOUT_SECONDS=150,
        ROSREESTR_CACHE_MODE='none',
        ROSREESTR_CACHE_TTL_SECONDS=100,
    )
    client = build_rosreestr_client(settings)
    assert isinstance(client, ApiCloudRosreestrClient)
