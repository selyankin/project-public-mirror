"""Use-case расчёта риск-карты по адресу."""

from __future__ import annotations

from dataclasses import dataclass

from checks.application.ports.checks import (
    AddressResolverPort,
    SignalsProviderPort,
)
from checks.domain.value_objects.address import (
    AddressNormalized,
    AddressRaw,
)
from risks.application.scoring import build_risk_card
from risks.domain.entities.risk_card import RiskCard, RiskSignal


@dataclass(slots=True)
class AddressRiskCheckResult:
    """Результат проверки риска для адреса."""

    normalized_address: AddressNormalized
    signals: list[RiskSignal]
    risk_card: RiskCard


class AddressRiskCheckUseCase:
    """Сценарий построения риск-карты по адресу."""

    __slots__ = ('_address_resolver', '_signals_provider')

    def __init__(
        self,
        *,
        address_resolver: AddressResolverPort,
        signals_provider: SignalsProviderPort,
    ) -> None:
        """Сохранить зависимости для нормализации и сигналов."""

        self._address_resolver = address_resolver
        self._signals_provider = signals_provider

    def execute(self, raw_address: AddressRaw) -> AddressRiskCheckResult:
        """Выполнить полный цикл нормализации и построения риска."""

        normalized = self._address_resolver.normalize(raw_address)
        signals_tuple = self._signals_provider.collect(normalized)
        risk_card = build_risk_card(signals_tuple)
        return AddressRiskCheckResult(
            normalized_address=normalized,
            signals=list(signals_tuple),
            risk_card=risk_card,
        )
