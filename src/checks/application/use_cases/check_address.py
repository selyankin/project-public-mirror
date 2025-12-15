"""Use-case проверки адресов и URL."""

from __future__ import annotations

from typing import Any

from src.checks.application.ports.checks import (
    AddressResolverPort,
    SignalsProviderPort,
)
from src.checks.domain.value_objects.address import normalize_address_raw
from src.checks.domain.value_objects.url import UrlRaw
from src.risks.application.scoring import build_risk_card
from src.risks.domain.entities.risk_card import RiskSignal
from src.risks.domain.helpers.signals import get_signal_definition


class CheckAddressUseCase:
    """Use-case для построения RiskCard по запросу пользователя."""

    __slots__ = ('_address_resolver', '_signals_provider')

    def __init__(
        self,
        address_resolver: AddressResolverPort,
        signals_provider: SignalsProviderPort,
    ):
        """Create use-case instance with required ports."""

        self._address_resolver = address_resolver
        self._signals_provider = signals_provider

    def execute(self, raw_query: str) -> dict[str, Any]:
        """Выполнить проверку и вернуть сериализованный RiskCard."""
        query = raw_query.strip()
        if query.lower().startswith(('http://', 'https://')):
            UrlRaw(query)
            definition = get_signal_definition('url_not_supported_yet')
            signals: tuple[RiskSignal, ...] = (
                RiskSignal(
                    {
                        'code': definition.code,
                        'title': definition.title,
                        'description': definition.description,
                        'severity': int(definition.severity),
                        'evidence_refs': ('rule:url_not_supported',),
                    },
                ),
            )

        else:
            raw_address = normalize_address_raw(raw_query)
            normalized = self._address_resolver.normalize(raw_address)
            signals = self._signals_provider.collect(normalized)

        risk_card = build_risk_card(signals)
        return risk_card.to_dict()
