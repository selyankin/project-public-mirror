"""Секция с базовым резюме отчёта."""

from __future__ import annotations

from typing import Any


async def build(check_payload: dict[str, Any]) -> dict[str, Any]:
    """Подготовить базовое резюме по нормализованному адресу."""

    normalized = check_payload.get('normalized_address') or {}
    risk = check_payload.get('risk_card') or {}
    return {
        'input_kind': check_payload.get('kind'),
        'raw_input': check_payload.get('raw_input'),
        'address': {
            'normalized': normalized.get('normalized'),
            'confidence': normalized.get('confidence'),
            'source': normalized.get('source'),
        },
        'risk_overview': {
            'score': risk.get('score'),
            'level': risk.get('level'),
            'summary': risk.get('summary'),
        },
    }
