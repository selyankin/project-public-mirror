"""Секция со списком риск-сигналов."""

from __future__ import annotations

from typing import Any


async def build(check_payload: dict[str, Any]) -> dict[str, Any]:
    """Вернуть сигналы, обнаруженные в чек-процессе."""

    return {
        'signals': check_payload.get('signals', []),
    }
