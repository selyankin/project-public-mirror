"""Извлечение сумм из текста судебного акта."""

from __future__ import annotations

import re

from sources.kad_arbitr.models import KadArbitrAmountsResult

_RESOLUTION_MARKERS = (
    'решил:',
    'определил:',
    'постановил:',
)

_MIN_AMOUNT = 1000

_PATTERNS = (
    re.compile(
        r'(\d[\d\s\u00a0\u2009]*)(?:[,.]\d{1,2})?\s*' r'(?:руб\.?|р\.|₽)',
        re.IGNORECASE,
    ),
    re.compile(
        r'(?:сумм[ауы]\s*)'
        r'(\d[\d\s\u00a0\u2009]*)(?:[,.]\d{1,2})?\s*'
        r'(?:руб\.?|р\.|₽)',
        re.IGNORECASE,
    ),
    re.compile(
        r'(?:взыскат[ья][^\d]{0,40})'
        r'(\d[\d\s\u00a0\u2009]*)(?:[,.]\d{1,2})?\s*'
        r'(?:руб\.?|р\.|₽)',
        re.IGNORECASE,
    ),
)


def normalize_text_for_amounts(value: str) -> str:
    """Нормализовать текст для поиска сумм."""

    lowered = value.lower().replace('ё', 'е')
    lowered = lowered.replace('\u00a0', ' ').replace('\u2009', ' ')
    return ' '.join(lowered.split())


def parse_amount_to_int(raw: str) -> int | None:
    """Распарсить сумму в целое число рублей."""

    cleaned = raw.replace('\u00a0', ' ').replace('\u2009', ' ').replace(' ', '')
    if not cleaned:
        return None

    for separator in (',', '.'):
        if separator in cleaned:
            cleaned = cleaned.split(separator, 1)[0]
            break

    if not cleaned.isdigit():
        return None

    try:
        amount = int(cleaned)
    except ValueError:
        return None

    if amount < _MIN_AMOUNT:
        return None

    return amount


def extract_amounts(
    *,
    text: str,
    max_amounts: int = 3,
) -> KadArbitrAmountsResult:
    """Извлечь суммы из текста."""

    normalized = normalize_text_for_amounts(text)
    relevant = _extract_relevant_text(normalized)
    matches = _collect_matches(relevant)
    if relevant != normalized:
        matches.extend(_collect_matches(normalized))

    if not matches:
        return KadArbitrAmountsResult(
            amounts=[],
            matched_fragments=[],
            notes='no amounts found',
        )

    unique: dict[int, str] = {}
    for amount, snippet in matches:
        if amount not in unique:
            unique[amount] = snippet

    sorted_items = sorted(
        unique.items(), key=lambda item: item[0], reverse=True
    )
    limited = sorted_items[:max_amounts]
    amounts = [item[0] for item in limited]
    fragments = [item[1] for item in limited]

    return KadArbitrAmountsResult(
        amounts=amounts,
        matched_fragments=fragments,
        notes=None,
    )


def _extract_relevant_text(text: str) -> str:
    """Вернуть текст резолютивной части, если он найден."""

    for marker in _RESOLUTION_MARKERS:
        index = text.find(marker)
        if index != -1:
            return text[index : index + 25000]
    return text


def _collect_matches(text: str) -> list[tuple[int, str]]:
    """Собрать совпадения сумм с фрагментами текста."""

    results: list[tuple[int, str]] = []
    for pattern in _PATTERNS:
        for match in pattern.finditer(text):
            amount = parse_amount_to_int(match.group(1))
            if amount is None:
                continue

            snippet = _build_snippet(text, match.start(), match.end())
            results.append(
                (
                    amount,
                    snippet,
                )
            )

    return results


def _build_snippet(text: str, start: int, end: int) -> str:
    """Собрать сниппет вокруг совпадения."""

    window = 120
    left = max(start - window, 0)
    right = min(end + window, len(text))
    snippet = text[left:right].strip()
    if len(snippet) > 300:
        snippet = snippet[:300]

    return snippet
