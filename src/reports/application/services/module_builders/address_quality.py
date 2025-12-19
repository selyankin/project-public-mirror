"""Секция с детализацией качества адреса."""

from __future__ import annotations

from typing import Any


async def build(check_payload: dict[str, Any]) -> dict[str, Any]:
    """Подготовить данные об адресе и нормализации."""

    normalized = check_payload.get('normalized_address') or {}
    return {
        'raw_input': check_payload.get('raw_input'),
        'normalized': normalized.get('normalized'),
        'confidence': normalized.get('confidence'),
        'source': normalized.get('source'),
        'tokens': list(normalized.get('tokens') or []),
    }
