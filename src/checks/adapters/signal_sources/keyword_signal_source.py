"""Источник сигналов на основе ключевых правил адреса."""

from __future__ import annotations

from collections.abc import Callable
from typing import Any

from src.checks.application.ports.signal_sources import SignalsSourcePort
from src.checks.domain.value_objects.address import AddressNormalized
from src.risks.domain.entities.risk_card import RiskSignal
from src.risks.domain.helpers.signals import get_signal_definition


class KeywordSignalSource(SignalsSourcePort):
    """Источник сигналов, работающий по ключевым словам."""

    __slots__ = (
        "_data",
        "_builders",
    )

    def __init__(self, data: dict[str, Any]):
        """Создать источник сигналов."""
        self._data = dict(data)
        self._builders: tuple[
            Callable[[AddressNormalized], RiskSignal | None],
            ...,
        ] = (
            self._rule_incomplete,
            self._rule_apartments,
            self._rule_hostel,
            self._rule_residential_complex,
        )

    def collect(self, normalized: AddressNormalized) -> tuple[RiskSignal, ...]:
        """Собрать сигналы, основанные на ключевых правилах."""

        signals: list[RiskSignal] = []
        for builder in self._builders:
            signal = builder(normalized)
            if signal is not None:
                signals.append(signal)

        return tuple(signals)

    def _rule_incomplete(
        self,
        address: AddressNormalized,
    ) -> RiskSignal | None:
        tokens = address.tokens
        has_number = any(ch.isdigit() for ch in address.normalized)
        if len(tokens) < 3 or not has_number:
            return self._build_signal(
                "address_incomplete",
                ("rule:address_incomplete",),
            )

        return None

    def _rule_apartments(
        self,
        normalized: AddressNormalized,
    ) -> RiskSignal | None:
        text = normalized.normalized
        if "апарт" in text or "apart" in text:
            return self._build_signal(
                "possible_apartments",
                ("rule:apartments_keyword",),
            )

        return None

    def _rule_hostel(
        self,
        normalized: AddressNormalized,
    ) -> RiskSignal | None:
        if "общежит" in normalized.normalized:
            return self._build_signal(
                "hostel_keyword",
                ("rule:hostel_keyword",),
            )

        return None

    def _rule_residential_complex(
        self,
        normalized: AddressNormalized,
    ) -> RiskSignal | None:
        if "жк" in normalized.tokens:
            return self._build_signal(
                "residential_complex_hint",
                ("rule:zhk_token",),
            )

        return None

    @staticmethod
    def _build_signal(
        code: str,
        evidence_refs: tuple[str, ...],
    ) -> RiskSignal:
        definition = get_signal_definition(code)
        return RiskSignal(
            {
                "code": definition.code,
                "title": definition.title,
                "description": definition.description,
                "severity": int(definition.severity),
                "evidence_refs": evidence_refs,
            },
        )
