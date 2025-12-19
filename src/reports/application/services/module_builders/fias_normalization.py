"""Секция с данными нормализации ФИАС."""

from __future__ import annotations

from typing import Any


async def build(check_payload: dict[str, Any]) -> dict[str, Any]:
    """Вернуть сырые данные ФИАС, если они есть."""

    fias_payload = check_payload.get('fias')
    return {
        'fias': fias_payload or {},
    }
