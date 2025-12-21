"""Секция с базовым резюме отчёта."""

from __future__ import annotations

from typing import Any

from reports.application.services.check_payload_reader import (
    CheckPayloadReader,
)


async def build(check_payload: dict[str, Any]) -> dict[str, Any]:
    """Сформировать краткое резюме по входному адресу."""

    reader = CheckPayloadReader(check_payload)
    normalized = reader.normalized_address()
    fias = reader.fias() or {}
    signals = reader.signals()
    score = reader.score()

    risk_level = _risk_level(score)
    highlights = _highlights(reader, normalized, fias, len(signals))

    return {
        'input': {
            'kind': reader.kind(),
            'value': reader.input_value(),
        },
        'address': {
            'normalized': normalized.get('normalized')
            or fias.get('normalized'),
            'fias_id': fias.get('fias_id') or fias.get('object_guid'),
        },
        'signals_count': len(signals),
        'risk_level': risk_level,
        'highlights': highlights[:5],
    }


def _risk_level(score: float | int | None) -> str:
    """Преобразовать скор в человекочитаемый уровень."""

    if score is None:
        return 'unknown'

    if score <= 30:
        return 'low'
    if score <= 70:
        return 'medium'
    return 'high'


def _highlights(
    reader: CheckPayloadReader,
    normalized: dict[str, Any],
    fias: dict[str, Any],
    signals_count: int,
) -> list[str]:
    """Сформировать короткие заметки по результату."""

    notes: list[str] = []
    if not fias:
        notes.append('Адрес не нормализован')

    if reader.kind() == 'url' and not normalized.get('normalized'):
        notes.append('Адрес из ссылки не извлечён')

    if signals_count > 0:
        notes.append(f'Найдено сигналов: {signals_count}')

    return notes
