"""Use-case проверки адресов и URL."""

from __future__ import annotations

from datetime import UTC, datetime
from typing import Any
from uuid import UUID

from checks.application.helpers.url_extraction import (
    extract_address_from_url,
)
from checks.application.ports.checks import CheckResultsRepoPort
from checks.application.use_cases.address_risk_check import (
    AddressRiskCheckResult,
    AddressRiskCheckUseCase,
)
from checks.domain.constants.enums.domain import QueryType
from checks.domain.entities.check_result import CheckResultSnapshot
from checks.domain.helpers.address_heuristics import is_address_like
from checks.domain.value_objects.address import normalize_address_raw
from checks.domain.value_objects.query import CheckQuery
from checks.domain.value_objects.url import UrlRaw
from risks.application.scoring import build_risk_card
from risks.domain.entities.risk_card import RiskSignal
from risks.domain.signals_catalog import get_signal_definition


class CheckAddressUseCase:
    """Use-case для построения RiskCard по запросу пользователя."""

    __slots__ = ('_address_risk_check_use_case', '_check_results_repo')

    def __init__(
        self,
        address_risk_check_use_case: AddressRiskCheckUseCase,
        check_results_repo: CheckResultsRepoPort,
    ):
        """Create use-case instance with required ports."""

        self._address_risk_check_use_case = address_risk_check_use_case
        self._check_results_repo = check_results_repo

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

        risk_result: AddressRiskCheckResult | None = None
        signals: tuple[RiskSignal, ...] = ()
        check_id: UUID | None = None

        if query.type is QueryType.address:
            if not is_address_like(query.query):
                signals = (
                    self._build_single_signal(
                        'query_not_address_like',
                        ('heuristic:address_like',),
                    ),
                )
            else:
                risk_result, signals = self._run_address_risk_check(
                    query.query,
                )
                check_id = self._store_check_result(query.query, risk_result)

        elif query.type is QueryType.url:
            url_vo = UrlRaw(query.query)
            extracted = extract_address_from_url(url_vo)
            if extracted and is_address_like(extracted):
                risk_result, signals = self._run_address_risk_check(
                    extracted,
                )
                check_id = self._store_check_result(extracted, risk_result)
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

        if risk_result is not None:
            risk_card = risk_result.risk_card
            normalized_address = risk_result.normalized_address
        else:
            risk_card = build_risk_card(signals)
            normalized_address = None

        result = risk_card.to_dict()
        result['address_confidence'] = (
            normalized_address.confidence if normalized_address else None
        )
        result['address_source'] = (
            normalized_address.source if normalized_address else None
        )
        result['check_id'] = check_id
        return result

    def _run_address_risk_check(
        self,
        raw_address: str,
    ) -> tuple[AddressRiskCheckResult, tuple[RiskSignal, ...]]:
        """Запустить сценарий риск-проверки адреса."""

        normalized_raw = normalize_address_raw(raw_address)
        result = self._address_risk_check_use_case.execute(normalized_raw)
        return result, tuple(result.signals)

    def _store_check_result(
        self,
        raw_input: str,
        result: AddressRiskCheckResult,
    ) -> UUID:
        """Сохранить результирующий снимок проверки."""

        snapshot = CheckResultSnapshot(
            raw_input=raw_input,
            normalized_address=result.normalized_address,
            signals=list(result.signals),
            risk_card=result.risk_card,
            created_at=datetime.now(UTC),
        )
        return self._check_results_repo.save(snapshot)

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
