"""Порты источников сигналов риска."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Protocol

from checks.domain.value_objects.address import AddressNormalized
from risks.domain.entities.risk_card import RiskSignal


@dataclass(slots=True)
class SignalsContext:
    """Контекст построения сигналов."""

    address: AddressNormalized | None = None


class SignalsSourcePort(Protocol):
    """Контракт для отдельного источника сигналов."""

    def collect(
        self,
        normalized: AddressNormalized,
        *,
        context: SignalsContext | None = None,
    ) -> tuple[RiskSignal, ...]:
        """Собрать сигналы из одного источника."""
