"""Упрощённый сигнал риска для вложенных payload."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Literal

SignalLevel = Literal['info', 'warning', 'good']


@dataclass(slots=True)
class SimpleRiskSignal:
    """Лёгкий сигнал с произвольными деталями."""

    code: str
    level: SignalLevel
    title: str
    details: dict[str, object] | None = None

    def to_dict(self) -> dict[str, object]:
        """Вернуть сериализуемое представление."""

        payload: dict[str, object] = {
            'code': self.code,
            'level': self.level,
            'title': self.title,
        }
        if self.details:
            payload['details'] = self.details

        return payload
