"""Извлечение исхода дела из PDF текста."""

from __future__ import annotations

import re

from sources.kad_arbitr.models import (
    KadArbitrActOutcomeNormalized,
    KadArbitrOutcomeConfidence,
    KadArbitrOutcomeType,
)

_BANKRUPT_DECLARED_RE = re.compile(r'признат[ьи]\s+банкрот', re.IGNORECASE)
_BANKRUPT_COMPETITION_RE = re.compile(
    r'ввест[ьи]\s+конкурсн\w*\s+производств', re.IGNORECASE
)
_BANKRUPT_OBSERVATION_RE = re.compile(r'ввест[ьи]\s+наблюден', re.IGNORECASE)
_SETTLEMENT_RE = re.compile(r'утверд\w*\s+миров', re.IGNORECASE)
_SATISFIED_RE = re.compile(
    r'иск\w*\s+требован\w*\s+удовлетворить', re.IGNORECASE
)
_SATISFIED_SHORT_RE = re.compile(r'удовлетворить\s+иск', re.IGNORECASE)
_DENIED_RE = re.compile(r'в\s+удовлетворени[ия]\s+.*отказ', re.IGNORECASE)
_DENIED_SHORT_RE = re.compile(r'отказ\w*\s+.*в\s+удовлетворени', re.IGNORECASE)
_PARTIAL_RE = re.compile(
    r'удовлетворить\s+частично|частично\s+удовлетворить',
    re.IGNORECASE,
)
_TERMINATED_RE = re.compile(r'прекрат\w*\s+производств', re.IGNORECASE)
_LEFT_RE = re.compile(r'остав\w*\s+без\s+рассмотрени', re.IGNORECASE)


def normalize_text(value: str) -> str:
    """Нормализовать текст для поиска."""

    lowered = value.lower().replace('ё', 'е')
    return re.sub(r'\s+', ' ', lowered).strip()


def find_with_context(
    text: str,
    pattern: re.Pattern[str],
    *,
    window: int = 220,
) -> tuple[str, str] | None:
    """Найти совпадение и вернуть фразу и контекст."""

    match = pattern.search(text)
    if not match:
        return None

    start, end = match.span()
    left = max(0, start - window)
    right = min(len(text), end + window)
    snippet = text[left:right].strip()
    return match.group(0), snippet


def extract_outcome_from_text(
    *,
    text: str,
) -> KadArbitrActOutcomeNormalized:
    """Определить исход по тексту судебного акта."""

    if not text or not text.strip():
        return _unknown_outcome(reason='empty text')

    normalized = normalize_text(text)

    result = _match_outcome(
        normalized,
        _BANKRUPT_DECLARED_RE,
        'bankruptcy_bankrupt_declared',
        'high',
    )
    if result:
        return result

    result = _match_outcome(
        normalized,
        _BANKRUPT_COMPETITION_RE,
        'bankruptcy_competition',
        'high',
    )
    if result:
        return result

    result = _match_outcome(
        normalized,
        _BANKRUPT_OBSERVATION_RE,
        'bankruptcy_observation',
        'high',
    )
    if result:
        return result

    result = _match_outcome(
        normalized,
        _SETTLEMENT_RE,
        'settlement_approved',
        'high',
    )
    if result:
        return result

    result = _match_outcome(
        normalized,
        _PARTIAL_RE,
        'partial',
        'high',
    )
    if result:
        return result

    result = _match_outcome(
        normalized,
        _SATISFIED_RE,
        'satisfied',
        'high',
    )
    if result:
        return result

    result = _match_outcome(
        normalized,
        _SATISFIED_SHORT_RE,
        'satisfied',
        'high',
    )
    if result:
        return result

    result = _match_outcome(
        normalized,
        _DENIED_RE,
        'denied',
        'high',
    )
    if result:
        return result

    result = _match_outcome(
        normalized,
        _DENIED_SHORT_RE,
        'denied',
        'high',
    )
    if result:
        return result

    result = _match_outcome(
        normalized,
        _TERMINATED_RE,
        'terminated',
        'medium',
    )
    if result:
        return result

    result = _match_outcome(
        normalized,
        _LEFT_RE,
        'left_without_review',
        'medium',
    )
    if result:
        return result

    return _unknown_outcome(reason='no patterns matched')


def _match_outcome(
    text: str,
    pattern: re.Pattern[str],
    outcome: KadArbitrOutcomeType,
    confidence: KadArbitrOutcomeConfidence,
) -> KadArbitrActOutcomeNormalized | None:
    """Построить результат при совпадении."""

    found = find_with_context(text, pattern)
    if not found:
        return None

    matched_phrase, snippet = found
    return KadArbitrActOutcomeNormalized(
        act_id='',
        outcome=outcome,
        confidence=confidence,
        matched_phrase=matched_phrase,
        evidence_snippet=snippet,
    )


def _unknown_outcome(*, reason: str) -> KadArbitrActOutcomeNormalized:
    """Сформировать неизвестный исход."""

    return KadArbitrActOutcomeNormalized(
        act_id='',
        outcome='unknown',
        confidence='low',
        reason=reason,
    )
