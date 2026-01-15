"""Фабрика клиентов kad.arbitr.ru."""

from __future__ import annotations

from shared.kernel.settings import Settings
from sources.kad_arbitr.cache import LruTtlCache
from sources.kad_arbitr.ports import KadArbitrClientPort
from sources.kad_arbitr.stub_client import StubKadArbitrClient

_KAD_ARBITR_CACHE: LruTtlCache | None = None


def build_kad_arbitr_client(
    *,
    settings: Settings,
) -> KadArbitrClientPort:
    """Построить клиента kad.arbitr.ru в зависимости от настроек."""

    mode = settings.KAD_ARBITR_MODE
    if mode == 'xhr':
        from sources.kad_arbitr.cache import LruTtlCache
        from sources.kad_arbitr.throttling import RateLimiter
        from sources.kad_arbitr.xhr_client import XhrKadArbitrClient

        rate_limiter = RateLimiter(
            min_interval_seconds=settings.KAD_ARBITR_RATE_LIMIT_SECONDS,
        )
        cache = None
        if settings.KAD_ARBITR_CACHE_ENABLED:
            global _KAD_ARBITR_CACHE
            if _KAD_ARBITR_CACHE is None:
                _KAD_ARBITR_CACHE = LruTtlCache(
                    max_items=settings.KAD_ARBITR_CACHE_MAX_ITEMS,
                    ttl_seconds=settings.KAD_ARBITR_CACHE_TTL_SECONDS,
                )
            cache = _KAD_ARBITR_CACHE

        return XhrKadArbitrClient(
            base_url=settings.KAD_ARBITR_BASE_URL,
            timeout_seconds=settings.KAD_ARBITR_TIMEOUT_SECONDS,
            ssl_verify=settings.KAD_ARBITR_SSL_VERIFY,
            user_agent=settings.KAD_ARBITR_USER_AGENT,
            rate_limiter=rate_limiter,
            cache=cache,
        )

    if mode == 'stub':
        return StubKadArbitrClient()

    raise ValueError('KAD_ARBITR_MODE must be one of: stub, xhr.')
