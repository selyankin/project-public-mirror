"""Проверка, что фабрика включает кэш Росреестра."""

from types import SimpleNamespace

from shared.kernel.rosreestr_client_factory import build_rosreestr_client
from sources.rosreestr.cached_client import CachedRosreestrClient


def test_factory_wraps_client_with_cache():
    settings = SimpleNamespace(
        ROSREESTR_MODE='stub',
        ROSREESTR_TOKEN=None,
        ROSREESTR_TIMEOUT_SECONDS=120,
        ROSREESTR_CACHE_MODE='memory',
        ROSREESTR_CACHE_TTL_SECONDS=100,
    )

    client = build_rosreestr_client(settings)

    assert isinstance(client, CachedRosreestrClient)
