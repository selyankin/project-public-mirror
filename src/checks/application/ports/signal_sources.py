"""Порты источников сигналов риска."""

from __future__ import annotations

from typing import Protocol

from src.checks.domain.value_objects.address import AddressNormalized
from src.risks.domain.entities.risk_card import RiskSignal


class SignalsSourcePort(Protocol):
    """Контракт для отдельного источника сигналов."""

    def collect(self, normalized: AddressNormalized) -> tuple[RiskSignal, ...]:
        """Собрать сигналы из одного источника."""
