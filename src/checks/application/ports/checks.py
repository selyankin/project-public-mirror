"""Application ports for check-related services."""

from typing import Protocol

from checks.domain.value_objects.address import (
    AddressNormalized,
    AddressRaw,
)
from risks.domain.entities.risk_card import RiskSignal


class AddressResolverPort(Protocol):
    """Порт сервиса нормализации адресов."""

    def normalize(self, raw: AddressRaw) -> AddressNormalized:
        """Преобразовать сырой адрес в каноничное представление."""


class SignalsProviderPort(Protocol):
    """Агрегирующий провайдер сигналов риска."""

    def collect(self, normalized: AddressNormalized) -> tuple[RiskSignal, ...]:
        """Собрать агрегированный набор сигналов по адресу."""
