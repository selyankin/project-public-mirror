"""Источник сигналов, основанный на confidence/source адреса."""

from __future__ import annotations

from typing import Any

from checks.application.ports.signal_sources import (
    SignalsContext,
    SignalsSourcePort,
)
from checks.domain.value_objects.address import AddressNormalized
from risks.domain.entities.risk_card import RiskSignal
from risks.domain.signals_catalog import get_signal_definition


class AddressConfidenceSignalSource(SignalsSourcePort):
    """Формирует сигналы по данным confidence/source адреса."""

    __slots__ = ()

    def __init__(self, _: dict[str, Any] | None = None) -> None:
        """Инициализация источника (параметры пока не требуются)."""
        pass

    def collect(
        self,
        normalized: AddressNormalized,
        *,
        context: SignalsContext | None = None,
    ) -> tuple[RiskSignal, ...]:
        """Сформировать сигналы по confidence/source."""

        address = (context.address if context else None) or normalized
        if address is None:
            return ()

        codes: list[str] = []
        if address.confidence == 'unknown':
            codes.append('address_confidence_unknown')
        elif address.confidence == 'low':
            codes.append('address_confidence_low')

        if address.source == 'stub':
            codes.append('address_source_stub')

        signals = [
            self._build_signal(
                code,
                address,
            )
            for code in codes
        ]
        return tuple(signals)

    @staticmethod
    def _build_signal(
        code: str,
        address: AddressNormalized,
    ) -> RiskSignal:

        definition = get_signal_definition(code)
        evidence = [
            f'address_confidence={address.confidence}',
            f'address_source={address.source}',
        ]

        return RiskSignal(
            {
                'code': definition.code,
                'title': definition.title,
                'description': definition.description,
                'severity': int(definition.severity),
                'evidence_refs': tuple(evidence),
            },
        )
