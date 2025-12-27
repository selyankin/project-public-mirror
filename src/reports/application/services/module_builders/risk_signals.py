"""Секция со списком риск-сигналов."""

from __future__ import annotations

from typing import Any

from reports.application.services.check_payload_reader import (
    CheckPayloadReader,
)


async def build(check_payload: dict[str, Any]) -> dict[str, Any]:
    """Нормализовать сигналы риска для отчёта."""

    reader = CheckPayloadReader(check_payload)
    items = [_normalize(signal) for signal in reader.signals()]
    return {
        'count': len(items),
        'items': items,
    }


def _normalize(signal: dict[str, Any]) -> dict[str, Any]:
    """Привести сигнал к единому виду."""

    code = str(signal.get('code') or 'unknown')
    title = signal.get('title') or code
    severity = _severity(signal.get('severity'))

    item: dict[str, Any] = {
        'code': code,
        'title': title,
        'severity': severity,
    }

    description = signal.get('description')
    if description:
        item['description'] = description

    evidence = signal.get('evidence') or signal.get('evidence_refs')
    if evidence:
        item['evidence'] = evidence

    return item


def _severity(raw: Any) -> str:
    """Преобразовать уровень важности в info/warning/critical."""

    if isinstance(raw, str):
        lowered = raw.lower()
        if lowered in {'critical', 'high', 'severe'}:
            return 'critical'
        if lowered in {'warning', 'medium'}:
            return 'warning'
        return 'info'

    if isinstance(raw, (int, float)):
        value = float(raw)
        if value >= 70:
            return 'critical'
        if value >= 40:
            return 'warning'
        return 'info'

    return 'info'
