"""Проверка кэширования текста PDF."""

import pytest

from sources.kad_arbitr.cache import LruTtlCache
from sources.kad_arbitr.models import KadArbitrJudicialActNormalized
from sources.kad_arbitr.use_cases.resolve_act_outcome import (
    ResolveKadArbitrActOutcome,
)


class _FetcherStub:
    def __init__(self) -> None:
        self.calls = 0

    async def fetch(self, *, url: str) -> bytes:
        self.calls += 1
        return b'pdf'


class _ExtractorStub:
    def __init__(self, text: str) -> None:
        self.text = text

    def extract_text(self, *, pdf_bytes: bytes) -> str:
        return self.text


pytestmark = pytest.mark.asyncio


async def test_text_cache_avoids_repeated_fetch() -> None:
    fetcher = _FetcherStub()
    extractor = _ExtractorStub(text='текст ' * 60)
    cache = LruTtlCache(max_items=10, ttl_seconds=60)
    use_case = ResolveKadArbitrActOutcome(
        fetcher=fetcher,
        text_extractor=extractor,
        text_cache=cache,
    )
    act = KadArbitrJudicialActNormalized(
        act_id='act-1',
        act_type='decision',
        pdf_url='https://kad.arbitr.ru/Document/Pdf/1',
    )

    await use_case.execute(act=act)
    await use_case.execute(act=act)

    assert fetcher.calls == 1
