"""Пайплайн агрегации сигналов из нескольких источников."""

from __future__ import annotations

from collections.abc import Iterable
from typing import Any

from src.checks.application.ports.signal_sources import SignalsSourcePort
from src.checks.domain.value_objects.address import AddressNormalized
from src.risks.domain.entities.risk_card import RiskSignal


class SignalsPipeline:
    """Пайплайн, объединяющий несколько источников сигналов."""

    __slots__ = ('_sources',)

    def __init__(self, data: dict[str, Any]):
        """Создать пайплайн с указанными источниками."""

        sources = data.get('sources')
        if not isinstance(sources, Iterable):
            raise ValueError('Не передан список источников сигналов.')

        sources_tuple = tuple(sources)
        if not sources_tuple:
            raise ValueError('Список источников сигналов не может быть пустым.')

        self._sources: tuple[SignalsSourcePort, ...] = sources_tuple

    def collect(self, normalized: AddressNormalized) -> tuple[RiskSignal, ...]:
        """Собрать сигналы со всех источников с дедупликацией."""

        collected: list[RiskSignal] = []
        seen_codes: set[str] = set()
        for source in self._sources:
            for signal in source.collect(normalized):
                if signal.code in seen_codes:
                    continue

                collected.append(signal)
                seen_codes.add(signal.code)

        return tuple(collected)
