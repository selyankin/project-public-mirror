"""Извлечение текста из PDF для kad.arbitr.ru."""

from __future__ import annotations

from io import BytesIO

from sources.kad_arbitr.pdf.ports import PdfTextExtractorPort


class PyPdfTextExtractor(PdfTextExtractorPort):
    """Извлечение текста через pypdf."""

    def extract_text(self, *, pdf_bytes: bytes) -> str:
        """Извлечь текст через pypdf."""

        try:
            from pypdf import PdfReader
        except ImportError as exc:  # pragma: no cover - optional
            raise RuntimeError('pypdf is not installed') from exc

        reader = PdfReader(BytesIO(pdf_bytes))
        parts: list[str] = []
        for page in reader.pages:
            parts.append(page.extract_text() or '')
        return '\n'.join(parts)


class PdfMinerTextExtractor(PdfTextExtractorPort):
    """Извлечение текста через pdfminer.six."""

    def extract_text(self, *, pdf_bytes: bytes) -> str:
        """Извлечь текст через pdfminer.six."""

        try:
            from pdfminer.high_level import extract_text
        except ImportError as exc:  # pragma: no cover - optional
            raise RuntimeError('pdfminer.six is not installed') from exc

        return extract_text(BytesIO(pdf_bytes)) or ''


class CompositePdfTextExtractor(PdfTextExtractorPort):
    """Комбинированный извлекатель текста."""

    def __init__(
        self,
        *,
        primary: PdfTextExtractorPort,
        fallback: PdfTextExtractorPort,
    ) -> None:
        """Сохранить извлекатели текста."""

        self._primary = primary
        self._fallback = fallback

    def extract_text(self, *, pdf_bytes: bytes) -> str:
        """Извлечь текст с fallback на второй парсер."""

        try:
            text = self._primary.extract_text(pdf_bytes=pdf_bytes)
        except Exception:
            text = ''

        if text and len(text.strip()) >= 200:
            return text

        try:
            fallback_text = self._fallback.extract_text(pdf_bytes=pdf_bytes)
        except Exception:
            fallback_text = ''

        if fallback_text and len(fallback_text.strip()) >= 200:
            return fallback_text

        return fallback_text or text
