"""Секция с детализацией качества адреса."""

from __future__ import annotations

from typing import Any

from reports.application.services.check_payload_reader import (
    CheckPayloadReader,
)


async def build(check_payload: dict[str, Any]) -> dict[str, Any]:
    """Проанализировать нормализацию адреса и дать рекомендации."""

    reader = CheckPayloadReader(check_payload)
    normalized = reader.normalized_address()
    fias = reader.fias()
    confidence = _extract_confidence(normalized, fias)

    is_normalized = bool(fias or normalized.get('normalized'))
    issues: list[str] = []
    recommendations: list[str] = []

    if not fias:
        issues.append('Не удалось нормализовать адрес')
        recommendations.append('Уточните адрес: город, улица, дом')

    if fias and confidence is None:
        issues.append('Уверенность не предоставлена')

    grade = _grade(confidence, fias is not None)

    if grade in {'C', 'D'} and not recommendations:
        recommendations.append('Проверьте корректность адреса.')

    if issues and not recommendations:
        recommendations.append('Перепроверьте введённые данные.')

    return {
        'is_normalized': is_normalized,
        'confidence': confidence,
        'quality_grade': grade,
        'issues': issues,
        'recommendations': recommendations,
    }


def _extract_confidence(
    normalized: dict[str, Any],
    fias: dict[str, Any] | None,
) -> float | None:
    """Получить числовое значение confidence, если возможно."""

    raw = None
    if fias:
        raw = fias.get('confidence')
    if raw is None:
        raw = normalized.get('confidence')

    if isinstance(raw, int | float):
        return float(raw)

    if isinstance(raw, str):
        mapping = {
            'exact': 1.0,
            'high': 0.85,
            'medium': 0.65,
            'low': 0.35,
        }
        lowered = raw.lower()
        if lowered in mapping:
            return mapping[lowered]
        try:
            return float(raw)
        except ValueError:
            return None

    return None


def _grade(confidence: float | None, has_fias: bool) -> str:
    """Определить оценку качества адреса."""

    if confidence is None:
        return 'B' if has_fias else 'D'

    if confidence >= 0.9:
        return 'A'
    if confidence >= 0.7:
        return 'B'
    if confidence >= 0.5:
        return 'C'
    return 'D'
