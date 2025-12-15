"""Эвристики для проверки, похожа ли строка на адрес."""

from __future__ import annotations

import re

from checks.domain.constants.address import ADDRESS_KEYWORDS
from checks.domain.exceptions.address import AddressHeuristicsError


def normalize_whitespace(text: str) -> str:
    """Нормализовать пробелы для проверки адреса."""

    if not isinstance(text, str):
        raise AddressHeuristicsError('Ожидалась строка для нормализации.')

    return re.sub(r'\s+', ' ', text.strip())


def is_address_like(text: str) -> bool:
    """Вернуть True, если строка похожа на почтовый адрес."""

    normalized = normalize_whitespace(text)
    if len(normalized) < 7:
        return False

    tokens = normalized.split(' ')
    if len(tokens) < 2:
        return False

    lower = normalized.lower()
    has_digit = any(ch.isdigit() for ch in lower)

    has_keyword = False
    for token in tokens:
        token_clean = token.strip('.,')
        if token_clean in ADDRESS_KEYWORDS:
            has_keyword = True
            break

    if not has_keyword:
        for key in ADDRESS_KEYWORDS:
            if len(key) > 2 and key in lower:
                has_keyword = True
                break

    allowed_extra = {',', '.', '-', '/'}
    special_count = sum(
        1
        for ch in normalized
        if not (ch.isalnum() or ch.isspace() or ch in allowed_extra)
    )

    if special_count / len(normalized) > 0.2:
        return False

    if not has_digit and not has_keyword:
        return False

    return True
