"""Фабрика клиентов Росреестра."""

from __future__ import annotations

from shared.kernel.settings import Settings
from sources.rosreestr.api_cloud_client import ApiCloudRosreestrClient
from sources.rosreestr.cache.in_memory import InMemoryTtlRosreestrCache
from sources.rosreestr.cached_client import CachedRosreestrClient
from sources.rosreestr.ports import RosreestrClientPort
from sources.rosreestr.stub_client import StubRosreestrClient

_cache: InMemoryTtlRosreestrCache | None = None


def build_rosreestr_client(settings: Settings) -> RosreestrClientPort:
    """Instantiate a Rosreestr client based on settings."""

    cache_mode = getattr(settings, 'ROSREESTR_CACHE_MODE', 'memory')
    cache_ttl = getattr(settings, 'ROSREESTR_CACHE_TTL_SECONDS', 86400)

    if settings.ROSREESTR_MODE == 'api_cloud':
        client: RosreestrClientPort = ApiCloudRosreestrClient(
            token=settings.ROSREESTR_TOKEN,
            timeout_seconds=settings.ROSREESTR_TIMEOUT_SECONDS,
        )

    else:
        client = StubRosreestrClient()

    if cache_mode == 'memory':
        global _cache
        if _cache is None:
            _cache = InMemoryTtlRosreestrCache()
        client = CachedRosreestrClient(
            inner=client,
            cache=_cache,
            ttl_seconds=cache_ttl,
        )

    return client
