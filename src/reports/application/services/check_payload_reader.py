"""Адаптер безопасного доступа к check payload."""

from __future__ import annotations

from typing import Any


class CheckPayloadReader:
    """Позволяет удобно извлекать данные из payload проверки."""

    __slots__ = ('_payload',)

    def __init__(self, payload: dict[str, Any] | None) -> None:
        """Сохранить исходный payload."""

        self._payload = payload or {}

    def kind(self) -> str | None:
        """Вернуть тип входных данных (address/url)."""

        value = self._payload.get('kind')
        return str(value) if value is not None else None

    def input_value(self) -> str | None:
        """Вернуть исходную строку адреса."""

        value = self._payload.get('raw_input')
        return str(value) if isinstance(value, str) else value

    def normalized_address(self) -> dict[str, Any]:
        """Вернуть блок нормализованного адреса."""

        value = self._payload.get('normalized_address')
        return dict(value) if isinstance(value, dict) else {}

    def fias(self) -> dict[str, Any] | None:
        """Вернуть данные FIAS, если они есть."""

        value = self._payload.get('fias')
        if isinstance(value, dict) and value:
            return value
        return None

    def signals(self) -> list[dict[str, Any]]:
        """Вернуть список сигналов риска."""

        raw = self._payload.get('signals')
        if not isinstance(raw, list):
            return []

        result: list[dict[str, Any]] = []
        for item in raw:
            if isinstance(item, dict):
                result.append(item)
        return result

    def score(self) -> float | int | None:
        """Вернуть числовой скор, если он есть."""

        risk_card = self._payload.get('risk_card')
        if not isinstance(risk_card, dict):
            return None

        value = risk_card.get('score')
        if isinstance(value, int | float):
            return value

        try:
            return float(value)
        except (TypeError, ValueError):
            return None

    def meta(self) -> dict[str, Any]:
        """Вернуть произвольные метаданные."""

        meta = self._payload.get('meta')
        return dict(meta) if isinstance(meta, dict) else {}
