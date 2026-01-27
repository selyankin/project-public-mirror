"""Проверка use-case определения исхода по акту."""

import pytest

from sources.kad_arbitr.models import KadArbitrJudicialActNormalized
from sources.kad_arbitr.use_cases.resolve_act_outcome import (
    ResolveKadArbitrActOutcome,
)


class _StubFetcher:
    async def fetch(self, *, url: str) -> bytes:
        return b'pdf-bytes'


class _StubExtractor:
    def __init__(self, *, text: str) -> None:
        self._text = text

    def extract_text(self, *, pdf_bytes: bytes) -> str:
        return self._text


pytestmark = pytest.mark.asyncio


async def test_resolve_act_outcome_denied() -> None:
    act = KadArbitrJudicialActNormalized(
        act_id='act-1',
        act_type='decision',
        pdf_url='https://kad.arbitr.ru/Document/Pdf/1',
    )
    extractor = _StubExtractor(
        text=('В удовлетворении отказать. ' + ('текст ' * 50))
    )
    use_case = ResolveKadArbitrActOutcome(
        fetcher=_StubFetcher(),
        text_extractor=extractor,
    )

    result = await use_case.execute(act=act)

    assert result.act_id == 'act-1'
    assert result.outcome == 'denied'


async def test_resolve_act_outcome_missing_pdf() -> None:
    act = KadArbitrJudicialActNormalized(
        act_id='act-2',
        act_type='decision',
        pdf_url=None,
    )
    extractor = _StubExtractor(text='В удовлетворении отказать.')
    use_case = ResolveKadArbitrActOutcome(
        fetcher=_StubFetcher(),
        text_extractor=extractor,
    )

    result = await use_case.execute(act=act)

    assert result.outcome == 'unknown'
    assert result.reason == 'pdf_url is missing'


async def test_resolve_act_outcome_truncates_text() -> None:
    act = KadArbitrJudicialActNormalized(
        act_id='act-3',
        act_type='decision',
        pdf_url='https://kad.arbitr.ru/Document/Pdf/3',
    )
    long_text = 'Решил: В удовлетворении отказать. ' + ('a' * 100_000)
    extractor = _StubExtractor(text=long_text)
    use_case = ResolveKadArbitrActOutcome(
        fetcher=_StubFetcher(),
        text_extractor=extractor,
    )

    result = await use_case.execute(act=act)

    assert result.outcome == 'denied'
    assert result.extracted_text is not None
    assert len(result.extracted_text) <= 30_000
