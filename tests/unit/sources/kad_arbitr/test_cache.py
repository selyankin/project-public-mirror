"""Проверка LRU TTL кэша."""

from sources.kad_arbitr.cache import LruTtlCache


def test_cache_set_get() -> None:
    now = [0.0]
    cache = LruTtlCache(max_items=10, ttl_seconds=60, now_fn=lambda: now[0])

    cache.set('key', 'value')

    assert cache.get('key') == 'value'


def test_cache_expires() -> None:
    now = [0.0]
    cache = LruTtlCache(max_items=10, ttl_seconds=10, now_fn=lambda: now[0])

    cache.set('key', 'value')
    now[0] = 11.0

    assert cache.get('key') is None


def test_cache_lru_eviction() -> None:
    now = [0.0]
    cache = LruTtlCache(max_items=2, ttl_seconds=60, now_fn=lambda: now[0])

    cache.set('a', 1)
    cache.set('b', 2)
    assert cache.get('a') == 1
    cache.set('c', 3)

    assert cache.get('b') is None
    assert cache.get('a') == 1
