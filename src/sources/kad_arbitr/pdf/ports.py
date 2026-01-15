"""Порты для работы с PDF kad.arbitr.ru."""

from __future__ import annotations

from typing import Protocol


class PdfFetcherPort(Protocol):
    """Контракт загрузчика PDF."""

    async def fetch(self, *, url: str) -> bytes:
        """Асинхронно загрузить PDF по ссылке."""


class PdfTextExtractorPort(Protocol):
    """Контракт извлечения текста из PDF."""

    def extract_text(self, *, pdf_bytes: bytes) -> str:
        """Извлечь текст из PDF."""
