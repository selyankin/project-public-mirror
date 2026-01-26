"""Классификатор предмета спора по тексту акта."""

from __future__ import annotations

import re

from sources.kad_arbitr.models import (
    KadArbitrClaimCategory,
    KadArbitrClaimCategoryResult,
)

_CATEGORY_RULES: tuple[
    tuple[KadArbitrClaimCategory, tuple[str, ...], str],
    ...,
] = (
    (
        'bankruptcy',
        (
            'банкрот',
            'конкурсн',
            'наблюден',
            'финансовый управляющий',
        ),
        'high',
    ),
    (
        'ddu_penalty',
        (
            'долев',
            'дду',
            '214-фз',
            'неустойк',
            'застройщик',
        ),
        'high',
    ),
    (
        'construction_quality',
        (
            'качество',
            'дефект',
            'недостатк',
            'строительн',
            'работ',
        ),
        'medium',
    ),
    (
        'utilities_and_management',
        (
            'управляющ',
            'тсж',
            'жкх',
            'коммунальн',
            'взнос',
            'содержание',
        ),
        'medium',
    ),
    (
        'rent_and_lease',
        (
            'аренд',
            'найм',
            'лизинг',
        ),
        'medium',
    ),
    (
        'contractor_dispute',
        (
            'подряд',
            'выполнен',
            'работ',
            'договор подряда',
        ),
        'medium',
    ),
    (
        'debt_collection',
        (
            'задолжен',
            'взыскан',
            'долг',
            'проценты',
            'неосновательн',
        ),
        'medium',
    ),
    (
        'land_and_property',
        (
            'земельн',
            'участок',
            'право собственности',
            'кадастров',
        ),
        'medium',
    ),
    (
        'corporate_dispute',
        (
            'участник общества',
            'доля',
            'корпоративн',
            'созыв',
            'решение собрания',
        ),
        'medium',
    ),
)

_CONFIDENCE_ORDER = {
    'high': 0,
    'medium': 1,
    'low': 2,
}

_RESOLUTION_MARKERS = (
    'решил:',
    'определил:',
    'постановил:',
)


def normalize_text(value: str) -> str:
    """Нормализовать текст для поиска ключевых слов."""

    lowered = value.lower().replace('ё', 'е')
    cleaned = re.sub(r'[^0-9a-zа-я\- ]+', ' ', lowered)
    return ' '.join(cleaned.split())


def extract_relevant_text(text: str) -> str:
    """Выделить релевантную часть текста."""

    for marker in _RESOLUTION_MARKERS:
        index = text.find(marker)
        if index != -1:
            return text[index : index + 25000]
    return text


def classify_claim(*, text: str) -> KadArbitrClaimCategoryResult:
    """Классифицировать предмет спора по тексту."""

    normalized = normalize_text(text)
    relevant = extract_relevant_text(normalized)
    matches: list[tuple[KadArbitrClaimCategory, str, list[str]]] = []
    matched_keywords: list[str] = []

    for category, keywords, confidence in _CATEGORY_RULES:
        found: list[str] = []
        for keyword in keywords:
            if keyword in relevant:
                found.append(keyword)
                matched_keywords.append(keyword)
        if found:
            matches.append((category, confidence, found))

    if not matches:
        return KadArbitrClaimCategoryResult(
            categories=['unknown'],
            confidence='low',
            matched_keywords=[],
            notes='no keywords matched',
        )

    matches.sort(key=lambda item: _CONFIDENCE_ORDER[item[1]])
    categories = [item[0] for item in matches]
    unique_keywords = _unique_preserve(matched_keywords)

    if len(categories) == 1:
        confidence = matches[0][1]
        notes = None
    else:
        confidence = 'medium'
        notes = 'multiple categories matched'

    return KadArbitrClaimCategoryResult(
        categories=categories,
        confidence=confidence,
        matched_keywords=unique_keywords,
        notes=notes,
    )


def _unique_preserve(values: list[str]) -> list[str]:
    """Вернуть список уникальных значений с сохранением порядка."""

    seen: set[str] = set()
    result: list[str] = []
    for item in values:
        if item in seen:
            continue
        seen.add(item)
        result.append(item)
    return result
