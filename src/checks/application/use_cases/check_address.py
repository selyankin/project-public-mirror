"""Use-case for checking addresses and building risk cards."""

from __future__ import annotations

from typing import Any

from src.checks.application.ports.checks import (
    AddressResolverPort,
    SignalsProviderPort,
)
from src.checks.domain.value_objects.address import normalize_address_raw
from src.risks.application.scoring import build_risk_card


class CheckAddressUseCase:
    """Execute address checks and return risk card data."""

    __slots__ = ("_address_resolver", "_signals_resolver")

    def __init__(
        self,
        address_resolver: AddressResolverPort,
        signals_resolver: SignalsProviderPort,
    ):
        """Create use-case instance with required ports."""

        self._address_resolver = address_resolver
        self._signals_resolver = signals_resolver

    def execute(self, raw_query: str) -> dict[str, Any]:
        """Run address check and return a serialized risk card payload."""

        raw_address = normalize_address_raw(raw_query)
        normalized = self._address_resolver.normalize(raw_address)
        signals = self._signals_resolver.collect(normalized)
        risk_card = build_risk_card(signals)

        return risk_card.to_dict()
