"""Заглушка агрегатора сигналов риска."""

from __future__ import annotations

from typing import Any

from checks.adapters.signal_sources.address_confidence_signal_source import (
    AddressConfidenceSignalSource,
)
from checks.adapters.signal_sources.keyword_signal_source import (
    KeywordSignalSource,
)
from checks.application.ports.signal_sources import SignalsContext
from checks.application.signals_pipeline import SignalsPipeline
from checks.domain.value_objects.address import AddressNormalized
from risks.domain.entities.risk_card import RiskSignal


class SignalsProviderStub:
    """Заглушка, агрегирующая сигналы через пайплайн источников."""

    __slots__ = ('_pipeline',)

    def __init__(self, data: dict[str, Any]):
        """Создать провайдер сигналов для тестовых сценариев."""
        raw_sources = data.get('sources')
        if raw_sources:
            sources = tuple(raw_sources)
        else:
            sources = (
                AddressConfidenceSignalSource({}),
                KeywordSignalSource({}),
            )

        self._pipeline = SignalsPipeline({'sources': sources})

    def collect(self, normalized: AddressNormalized) -> tuple[RiskSignal, ...]:
        """Собрать сигналы адреса через встроенный пайплайн."""

        context = SignalsContext(address=normalized)
        return self._pipeline.collect(normalized, context=context)
