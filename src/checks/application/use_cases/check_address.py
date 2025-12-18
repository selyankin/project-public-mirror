"""Use-case проверки адресов и URL."""

from __future__ import annotations

from datetime import UTC, datetime
from typing import Any
from uuid import UUID

from checks.application.helpers.url_extraction import (
    extract_address_from_url,
)
from checks.application.ports.checks import (
    CheckCacheRepoPort,
    CheckResultsRepoPort,
)
from checks.application.use_cases.address_risk_check import (
    AddressRiskCheckResult,
    AddressRiskCheckUseCase,
)
from checks.domain.constants.enums.domain import QueryType
from checks.domain.entities.check_result import CheckResultSnapshot
from checks.domain.helpers.address_heuristics import is_address_like
from checks.domain.helpers.idempotency import build_check_cache_key
from checks.domain.value_objects.address import (
    AddressNormalized,
    normalize_address_raw,
)
from checks.domain.value_objects.query import CheckQuery
from checks.domain.value_objects.url import UrlRaw
from risks.application.scoring import build_risk_card
from risks.domain.entities.risk_card import RiskCard, RiskSignal
from risks.domain.signals_catalog import get_signal_definition


class CheckAddressUseCase:
    """Use-case для построения RiskCard по запросу пользователя."""

    __slots__ = (
        '_address_risk_check_use_case',
        '_check_results_repo',
        '_check_cache_repo',
        '_fias_mode',
        '_cache_version',
    )

    def __init__(
        self,
        address_risk_check_use_case: AddressRiskCheckUseCase,
        check_results_repo: CheckResultsRepoPort,
        check_cache_repo: CheckCacheRepoPort,
        *,
        fias_mode: str,
        cache_version: str,
    ):
        """Create use-case instance with required ports."""

        self._address_risk_check_use_case = address_risk_check_use_case
        self._check_results_repo = check_results_repo
        self._check_cache_repo = check_cache_repo
        self._fias_mode = fias_mode
        self._cache_version = cache_version

    async def execute(self, raw_query: str) -> dict[str, Any]:
        """Выполнить проверку по строке адреса (устаревший формат)."""

        return await self.execute_query(
            CheckQuery(
                {
                    'type': QueryType.address.value,
                    'query': raw_query,
                }
            ),
        )

    async def execute_query(self, query: CheckQuery) -> dict[str, Any]:
        """Выполнить проверку для типизированного запроса."""

        snapshot: CheckResultSnapshot | None = None
        risk_result: AddressRiskCheckResult | None = None
        check_id: UUID | None = None

        if query.type is QueryType.address:
            (
                snapshot,
                check_id,
                risk_result,
                signals,
            ) = await self._process_address(
                query.query,
            )

        elif query.type is QueryType.url:
            (
                snapshot,
                check_id,
                risk_result,
                signals,
            ) = await self._process_url(
                query.query,
            )

        else:
            signals = (
                self._build_single_signal(
                    'query_type_not_supported',
                    ('rule:query_type_not_supported',),
                ),
            )

        if snapshot is not None:
            risk_card = snapshot.risk_card
            normalized_address = snapshot.normalized_address
        elif risk_result is not None:
            risk_card = risk_result.risk_card
            normalized_address = risk_result.normalized_address
        else:
            risk_card = build_risk_card(signals)
            normalized_address = None

        return self._build_response(risk_card, normalized_address, check_id)

    async def _process_address(self, text: str) -> tuple[
        CheckResultSnapshot | None,
        UUID | None,
        AddressRiskCheckResult | None,
        tuple[RiskSignal, ...],
    ]:
        """Обработать адресный запрос с учётом кэша."""

        if not is_address_like(text):
            signals = (
                self._build_single_signal(
                    'query_not_address_like',
                    ('heuristic:address_like',),
                ),
            )
            return None, None, None, signals

        normalized_input = normalize_address_raw(text).value
        cache_key = self._build_cache_key(
            input_kind='address',
            input_value=normalized_input,
        )
        cached = await self._get_cached_snapshot(cache_key)
        if cached:
            return cached[0], cached[1], None, ()

        risk_result, signals = self._run_address_risk_check(text)
        snapshot, check_id = await self._store_check_result(
            normalized_input,
            risk_result,
            kind='address',
        )
        await self._check_cache_repo.set(cache_key, check_id)
        return snapshot, check_id, risk_result, signals

    async def _process_url(self, url_text: str) -> tuple[
        CheckResultSnapshot | None,
        UUID | None,
        AddressRiskCheckResult | None,
        tuple[RiskSignal, ...],
    ]:
        """Обработать запрос URL и учесть кэш."""

        normalized_input = self._sanitize_input_value(url_text)
        cache_key = self._build_cache_key(
            input_kind='url',
            input_value=normalized_input,
        )
        cached = await self._get_cached_snapshot(cache_key)
        if cached:
            return cached[0], cached[1], None, ()

        url_vo = UrlRaw(url_text)
        extracted = extract_address_from_url(url_vo)
        if extracted and is_address_like(extracted):
            normalized_address_input = normalize_address_raw(extracted).value
            risk_result, signals = self._run_address_risk_check(extracted)
            snapshot, check_id = await self._store_check_result(
                normalized_address_input,
                risk_result,
                kind='url',
            )
            await self._check_cache_repo.set(cache_key, check_id)
            return snapshot, check_id, risk_result, signals

        signals = (
            self._build_single_signal(
                'url_not_supported_yet',
                ('rule:url_not_supported',),
            ),
        )
        return None, None, None, signals

    def _build_cache_key(
        self,
        *,
        input_kind: str,
        input_value: str,
    ) -> str:
        """Построить ключ кэша для проверки."""

        return build_check_cache_key(
            input_kind=input_kind,  # type: ignore[arg-type]
            input_value=input_value,
            fias_mode=self._fias_mode,
            version=self._cache_version,
        )

    async def _get_cached_snapshot(
        self,
        cache_key: str,
    ) -> tuple[CheckResultSnapshot, UUID] | None:
        """Проверить кэш и вернуть снапшот."""

        entry = await self._check_cache_repo.get(cache_key)
        if not entry:
            return None
        snapshot = await self._check_results_repo.get(entry.check_id)
        if snapshot is None:
            return None
        return snapshot, entry.check_id

    @staticmethod
    def _build_response(
        risk_card: RiskCard,
        normalized_address: AddressNormalized | None,
        check_id: UUID | None,
    ) -> dict[str, Any]:
        """Сформировать ответ API из риск-карты и адреса."""

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

    async def _store_check_result(
        self,
        raw_input: str,
        result: AddressRiskCheckResult,
        *,
        kind: str,
    ) -> tuple[CheckResultSnapshot, UUID]:
        """Сохранить результирующий снимок проверки."""

        snapshot = CheckResultSnapshot(
            raw_input=raw_input,
            normalized_address=result.normalized_address,
            signals=list(result.signals),
            risk_card=result.risk_card,
            created_at=datetime.now(UTC),
            kind=kind,
        )
        check_id = await self._check_results_repo.save(snapshot)
        return snapshot, check_id

    @staticmethod
    def _sanitize_input_value(value: str) -> str:
        """Свести строку к единообразному виду для ключа кэша."""

        return ' '.join(value.strip().split())

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
