"""Use-case проверки адресов и URL."""

from __future__ import annotations

from typing import Any

from checks.application.helpers.url_extraction import (
    extract_address_from_url,
)
from checks.application.ports.checks import (
    AddressResolverPort,
    SignalsProviderPort,
)
from checks.domain.constants.enums.domain import QueryType
from checks.domain.helpers.address_heuristics import is_address_like
from checks.domain.value_objects.address import normalize_address_raw
from checks.domain.value_objects.query import CheckQuery
from checks.domain.value_objects.url import UrlRaw
from risks.application.scoring import build_risk_card
from risks.domain.entities.risk_card import RiskSignal
from risks.domain.signals_catalog import get_signal_definition


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
        """Выполнить проверку по строке адреса (устаревший формат)."""

        return self.execute_query(
            CheckQuery(
                {
                    'type': QueryType.address.value,
                    'query': raw_query,
                }
            ),
        )

    def execute_query(self, query: CheckQuery) -> dict[str, Any]:
        """Выполнить проверку для типизированного запроса."""

        if query.type is QueryType.address:
            if not is_address_like(query.query):
                signals = (
                    self._build_single_signal(
                        'query_not_address_like',
                        ('heuristic:address_like',),
                    ),
                )
            else:
                signals = self._collect_address_signals(query.query)

        elif query.type is QueryType.url:
            url_vo = UrlRaw(query.query)
            extracted = extract_address_from_url(url_vo)
            if extracted and is_address_like(extracted):
                signals = self._collect_address_signals(extracted)
            else:
                signals = (
                    self._build_single_signal(
                        'url_not_supported_yet',
                        ('rule:url_not_supported',),
                    ),
                )

        else:
            signals = (
                self._build_single_signal(
                    'query_type_not_supported',
                    ('rule:query_type_not_supported',),
                ),
            )

        risk_card = build_risk_card(signals)
        return risk_card.to_dict()

    def _collect_address_signals(
        self,
        raw_address: str,
    ) -> tuple[RiskSignal, ...]:
        """Собрать сигналы по строке адреса."""

        normalized_raw = normalize_address_raw(raw_address)
        normalized = self._address_resolver.normalize(normalized_raw)
        return self._signals_provider.collect(normalized)

    @staticmethod
    def _build_single_signal(
        code: str,
        evidence: tuple[str, ...],
    ) -> RiskSignal:
        """Создать единичный сигнал по коду справочника."""

        definition = get_signal_definition(code)
        return RiskSignal(
            {
                'code': definition.code,
                'title': definition.title,
                'description': definition.description,
                'severity': int(definition.severity),
                'evidence_refs': evidence,
            },
        )
