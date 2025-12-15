"""Заглушка агрегатора сигналов риска."""

from __future__ import annotations

from typing import Any

from src.checks.adapters.signal_sources.keyword_signal_source import (
    KeywordSignalSource,
)
from src.checks.application.signals_pipeline import SignalsPipeline
from src.checks.domain.value_objects.address import AddressNormalized
from src.risks.domain.entities.risk_card import RiskSignal


class SignalsProviderStub:
    """Заглушка, агрегирующая сигналы через пайплайн источников."""

    __slots__ = ('_pipeline',)

    def __init__(self, data: dict[str, Any]):
        """Создать провайдер сигналов для тестовых сценариев."""
        raw_sources = data.get('sources')
        if raw_sources:
            sources = tuple(raw_sources)
        else:
            sources = (KeywordSignalSource({}),)

        self._pipeline = SignalsPipeline({'sources': sources})

    def collect(self, normalized: AddressNormalized) -> tuple[RiskSignal, ...]:
        """Собрать сигналы адреса через встроенный пайплайн."""

        return self._pipeline.collect(normalized)
