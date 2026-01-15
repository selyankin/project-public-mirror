"""Парсер HTML карточки дела kad.arbitr.ru."""

from __future__ import annotations

import html
import re

from sources.kad_arbitr.models import (
    KadArbitrCaseDetailsNormalized,
    KadArbitrParticipantNormalized,
    normalize_inn,
    normalize_ogrn,
)

_CASE_NUMBER_RE = re.compile(r'([АA]\d{1,3}-\d+/\d{4})')
_INN_RE = re.compile(r'ИНН\s*[:№]?\s*([0-9]{10,12})', re.IGNORECASE)
_OGRN_RE = re.compile(r'ОГРН\s*[:№]?\s*([0-9]{13,15})', re.IGNORECASE)
_ROLE_MARKERS = (
    'истец',
    'ответчик',
    'третье лицо',
    'треть',
    'заявитель',
    'должник',
    'кредитор',
)


def parse_case_card_html(
    *,
    case_id: str,
    html: str,
    base_url: str = 'https://kad.arbitr.ru',
) -> KadArbitrCaseDetailsNormalized:
    """Распарсить HTML карточки дела."""

    card_url = f'{base_url.rstrip("/")}/Card/{case_id}'
    text = _strip_html(html)
    case_number = _extract_case_number(text)
    court = _extract_court(text)
    participants = _extract_participants(text)

    return KadArbitrCaseDetailsNormalized(
        case_id=case_id,
        case_number=case_number,
        court=court,
        participants=participants,
        card_url=card_url,
    )


def _strip_html(source: str) -> str:
    """Свести HTML к тексту."""

    cleaned = re.sub(
        r'<\s*/\s*(div|p|li|tr)\s*>',
        '\n',
        source,
        flags=re.IGNORECASE,
    )
    cleaned = re.sub(
        r'<\s*br\s*/?\s*>',
        '\n',
        cleaned,
        flags=re.IGNORECASE,
    )
    cleaned = re.sub(
        r'<\s*(div|p|li|tr)(\s+[^>]*)?>',
        '\n',
        cleaned,
        flags=re.IGNORECASE,
    )
    cleaned = re.sub(r'<[^>]+>', ' ', cleaned)
    cleaned = html.unescape(cleaned)
    cleaned = re.sub(r'[ \t]+', ' ', cleaned)
    cleaned = re.sub(r'\n+', '\n', cleaned)
    return cleaned.strip()


def _extract_case_number(text: str) -> str | None:
    """Извлечь номер дела."""

    match = _CASE_NUMBER_RE.search(text)
    if match:
        return match.group(1)
    return None


def _extract_court(text: str) -> str | None:
    """Извлечь наименование суда."""

    for line in text.splitlines():
        if 'арбитражный суд' in line.lower():
            return line.strip()

    return None


def _extract_participants(
    text: str,
) -> list[KadArbitrParticipantNormalized]:
    """Извлечь участников дела."""

    participants: list[KadArbitrParticipantNormalized] = []
    segments = _segment_participants(text)
    for segment in segments:
        lower = segment.lower()
        if not _has_role_marker(lower):
            continue

        role = _map_role(lower)
        name = _extract_name_from_segment(segment)
        inn = normalize_inn(_extract_inn(segment))
        ogrn = normalize_ogrn(_extract_ogrn(segment))
        if not name:
            continue

        participants.append(
            KadArbitrParticipantNormalized(
                name=name,
                role=role,
                inn=inn,
                ogrn=ogrn,
            )
        )

    return participants


def _has_role_marker(text: str) -> bool:
    """Проверить наличие маркера роли."""

    return any(marker in text for marker in _ROLE_MARKERS)


def _map_role(text: str) -> str:
    """Сопоставить роль участника."""

    if 'истец' in text:
        return 'plaintiff'
    if 'ответчик' in text:
        return 'defendant'
    if 'заявитель' in text:
        return 'plaintiff'
    if 'должник' in text:
        return 'defendant'
    if 'кредитор' in text:
        return 'plaintiff'
    if 'треть' in text:
        return 'third_party'
    return 'other'


def _extract_name_from_segment(segment: str) -> str | None:
    """Извлечь имя участника из сегмента."""

    lines = [part.strip() for part in segment.splitlines() if part.strip()]
    if not lines:
        return None

    first = lines[0]
    if ':' in first:
        name = first.split(':', 1)[1].strip()
        return name or None

    lower = first.lower()
    for marker in _ROLE_MARKERS:
        if lower.startswith(marker):
            candidate = first[len(marker) :].strip(' :')
            return candidate or None

    parts = first.split(' ', 1)
    if len(parts) > 1:
        candidate = parts[1].strip()
        return candidate or None

    return None


def _extract_inn(line: str) -> str | None:
    """Извлечь ИНН."""

    match = _INN_RE.search(line)
    if match:
        return match.group(1)
    return None


def _extract_ogrn(line: str) -> str | None:
    """Извлечь ОГРН."""

    match = _OGRN_RE.search(line)
    if match:
        return match.group(1)
    return None


def _segment_participants(text: str) -> list[str]:
    """Сегментировать текст по блокам участников."""

    lines = [line.strip() for line in text.splitlines() if line.strip()]
    segments: list[str] = []
    current: list[str] = []

    for line in lines:
        lower = line.lower()
        if _has_role_marker(lower):
            if current:
                segments.append('\n'.join(current))
                current = []
        current.append(line)

    if current:
        segments.append('\n'.join(current))

    return segments
