"""Парсер HTML со списком судебных актов kad.arbitr.ru."""

from __future__ import annotations

import html as html_lib
import re
from datetime import date

from sources.kad_arbitr.models import (
    KadArbitrCaseActsNormalized,
    KadArbitrJudicialActNormalized,
    map_act_type,
    parse_ru_date,
)

_ACT_TYPE_RE = re.compile(
    r'(Решение|Определение|Постановление|Судебный акт)',
    re.IGNORECASE,
)
_DATE_RE = re.compile(r'(\d{2}\.\d{2}\.\d{4})')
_PDF_URL_RE = re.compile(
    r'(https?://[^\s\'"]+/Document/Pdf/[^\s\'"]+)',
    re.IGNORECASE,
)
_PDF_URL_REL_RE = re.compile(
    r'(/Document/Pdf/[^\s\'"]+)',
    re.IGNORECASE,
)
_DOC_ID_RE = re.compile(
    r'(?:data-id|data-doc-id|document-)\s*["\']?(\d+)',
    re.IGNORECASE,
)


def parse_case_acts_html(
    *,
    case_id: str,
    html: str,
    base_url: str = 'https://kad.arbitr.ru',
) -> KadArbitrCaseActsNormalized:
    """Распарсить HTML со списком судебных актов."""

    card_url = f'{base_url.rstrip("/")}/Card/{case_id}'
    acts = _extract_acts(html=html, base_url=base_url, case_id=case_id)

    return KadArbitrCaseActsNormalized(
        case_id=case_id,
        card_url=card_url,
        acts=acts,
    )


def _extract_acts(
    *,
    html: str,
    base_url: str,
    case_id: str,
) -> list[KadArbitrJudicialActNormalized]:
    """Извлечь список актов из HTML."""

    acts: list[KadArbitrJudicialActNormalized] = []
    for match in _iter_pdf_urls(html=html, base_url=base_url):
        context = _extract_context(html, match.start(), match.end())
        act_type_raw = _extract_act_type(context)
        act_date = _extract_date(context)
        act_id = _extract_act_id_from_url(match.url)
        title = _extract_title(context)

        if act_id is None:
            continue

        acts.append(
            KadArbitrJudicialActNormalized(
                act_id=act_id,
                act_type=map_act_type(act_type_raw),
                act_type_raw=act_type_raw,
                act_date=act_date,
                pdf_url=match.pdf_url,
                raw_url=match.raw_url,
                title=title,
            )
        )

    if acts:
        return acts

    text = _strip_html(html)
    for line in text.splitlines():
        if not _ACT_TYPE_RE.search(line):
            continue

        act_type_raw = _extract_act_type(line)
        act_date = _extract_date(line)
        doc_id = _extract_doc_id(line)
        pdf_url = None
        if doc_id:
            pdf_url = _build_pdf_url(
                base_url=base_url,
                case_id=case_id,
                act_id=doc_id,
            )
        title = _extract_title(line)
        acts.append(
            KadArbitrJudicialActNormalized(
                act_id=doc_id or f'{case_id}:{len(acts) + 1}',
                act_type=map_act_type(act_type_raw),
                act_type_raw=act_type_raw,
                act_date=act_date,
                pdf_url=pdf_url,
                raw_url=None,
                title=title,
            )
        )

    return acts


class _PdfMatch:
    """Результат поиска PDF ссылки."""

    def __init__(
        self,
        *,
        url: str,
        pdf_url: str | None,
        raw_url: str | None,
        start: int,
        end: int,
    ) -> None:
        self.url = url
        self.pdf_url = pdf_url
        self.raw_url = raw_url
        self.start = start
        self.end = end


def _iter_pdf_urls(
    *,
    html: str,
    base_url: str,
) -> list[_PdfMatch]:
    """Найти ссылки на PDF."""

    matches: list[_PdfMatch] = []
    for match in _PDF_URL_RE.finditer(html):
        url = match.group(1)
        matches.append(
            _PdfMatch(
                url=url,
                pdf_url=url,
                raw_url=url,
                start=match.start(1),
                end=match.end(1),
            )
        )

    for match in _PDF_URL_REL_RE.finditer(html):
        url = match.group(1)
        pdf_url = f'{base_url.rstrip("/")}{url}'
        matches.append(
            _PdfMatch(
                url=url,
                pdf_url=pdf_url,
                raw_url=pdf_url,
                start=match.start(1),
                end=match.end(1),
            )
        )

    return matches


def _extract_act_id_from_url(url: str) -> str | None:
    """Вытащить идентификатор акта из URL."""

    if '/Document/Pdf/' not in url:
        return None

    tail = url.split('/Document/Pdf/', 1)[1]
    parts = tail.split('/')
    if len(parts) < 2:
        return None
    act_id = parts[1]
    return act_id or None


def _extract_doc_id(text: str) -> str | None:
    """Вытащить идентификатор документа из текста."""

    match = _DOC_ID_RE.search(text)
    if match:
        return match.group(1)
    return None


def _build_pdf_url(
    *,
    base_url: str,
    case_id: str,
    act_id: str,
) -> str:
    """Собрать PDF ссылку по идентификаторам."""

    return (
        f'{base_url.rstrip("/")}/Document/Pdf/'
        f'{case_id}/{act_id}/?isAddStamp=True'
    )


def _extract_context(html: str, start: int, end: int) -> str:
    """Достать контекст вокруг ссылки."""

    left = max(0, start - 200)
    right = min(len(html), end + 200)
    return _strip_html(html[left:right])


def _strip_html(source: str) -> str:
    """Свести HTML к тексту."""

    cleaned = re.sub(r'<[^>]+>', ' ', source)
    cleaned = html_lib.unescape(cleaned)
    cleaned = re.sub(r'[ \t]+', ' ', cleaned)
    cleaned = re.sub(r'\n+', '\n', cleaned)
    return cleaned.strip()


def _extract_act_type(text: str) -> str | None:
    """Извлечь тип акта."""

    match = _ACT_TYPE_RE.search(text)
    if match:
        return match.group(1)
    return None


def _extract_date(text: str) -> date | None:
    """Извлечь дату акта."""

    match = _DATE_RE.search(text)
    if match:
        return parse_ru_date(match.group(1))
    return None


def _extract_title(text: str) -> str | None:
    """Извлечь заголовок акта."""

    trimmed = text.strip()
    if trimmed:
        return trimmed[:200]
    return None
