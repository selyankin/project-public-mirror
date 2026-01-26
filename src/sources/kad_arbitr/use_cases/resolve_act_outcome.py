"""Use-case получения исхода судебного акта."""

from __future__ import annotations

from sources.kad_arbitr.cache import LruTtlCache
from sources.kad_arbitr.models import (
    KadArbitrActOutcomeNormalized,
    KadArbitrJudicialActNormalized,
)
from sources.kad_arbitr.pdf.outcome_extractor import (
    extract_outcome_from_text,
)
from sources.kad_arbitr.pdf.ports import PdfFetcherPort, PdfTextExtractorPort


class ResolveKadArbitrActOutcome:
    """Use-case определения исхода по судебному акту."""

    def __init__(
        self,
        *,
        fetcher: PdfFetcherPort,
        text_extractor: PdfTextExtractorPort,
        text_cache: LruTtlCache | None = None,
    ) -> None:
        """Сохранить зависимости use-case."""

        self._fetcher = fetcher
        self._text_extractor = text_extractor
        self._text_cache = text_cache

    async def execute(
        self,
        *,
        act: KadArbitrJudicialActNormalized,
    ) -> KadArbitrActOutcomeNormalized:
        """Определить исход по судебному акту."""

        if act.pdf_url is None:
            return KadArbitrActOutcomeNormalized(
                act_id=act.act_id,
                outcome='unknown',
                confidence='low',
                reason='pdf_url is missing',
                extracted_text=None,
            )

        cache_key = ('pdf_text', act.pdf_url)
        cached_text = (
            self._text_cache.get(cache_key)
            if self._text_cache is not None
            else None
        )
        if cached_text is None:
            pdf_bytes = await self._fetcher.fetch(url=act.pdf_url)
            text = self._text_extractor.extract_text(pdf_bytes=pdf_bytes)
            if self._text_cache is not None:
                self._text_cache.set(cache_key, text)
        else:
            text = cached_text

        if not text or len(text.strip()) < 200:
            return KadArbitrActOutcomeNormalized(
                act_id=act.act_id,
                outcome='unknown',
                confidence='low',
                reason='empty extracted text',
                extracted_text=None,
            )

        outcome = extract_outcome_from_text(text=text)
        outcome.act_id = act.act_id
        outcome.extracted_text = text
        return outcome
