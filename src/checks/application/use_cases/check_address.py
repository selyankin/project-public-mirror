"""Use-case проверки адресов и URL."""

from __future__ import annotations

from typing import Any
from uuid import UUID

from checks.application.ports.checks import (
    CheckCacheRepoPort,
    CheckResultsRepoPort,
)
from checks.application.ports.fias_client import FiasClient
from checks.application.use_cases.address_risk_check import (
    AddressRiskCheckResult,
    AddressRiskCheckUseCase,
)
from checks.application.use_cases.check_address_flow import (
    process_address,
    process_url,
)
from checks.application.use_cases.check_address_results import (
    build_response,
    store_check_result,
)
from checks.application.use_cases.check_address_signals import (
    build_single_signal,
)
from checks.application.use_cases.check_address_sources import (
    build_gis_gkh_payload,
    build_rosreestr_payload,
    fetch_fias_data,
)
from checks.domain.constants.enums.domain import QueryType
from checks.domain.entities.check_result import CheckResultSnapshot
from checks.domain.value_objects.address import (
    AddressNormalized,
    normalize_address_raw,
)
from checks.domain.value_objects.query import CheckQuery
from checks.infrastructure.listing_resolver_container import (
    get_listing_resolver_use_case,
)
from risks.application.scoring import build_risk_card
from risks.domain.entities.risk_card import RiskCard, RiskSignal
from shared.kernel.settings import Settings
from sources.gis_gkh.models import GisGkhHouseNormalized
from sources.rosreestr.models import RosreestrHouseNormalized


class CheckAddressUseCase:
    """Use-case для построения RiskCard по запросу пользователя."""

    __slots__ = (
        '_address_risk_check_use_case',
        '_check_results_repo',
        '_check_cache_repo',
        '_fias_client',
        '_fias_mode',
        '_cache_version',
        '_settings',
    )

    def __init__(
        self,
        address_risk_check_use_case: AddressRiskCheckUseCase,
        check_results_repo: CheckResultsRepoPort,
        check_cache_repo: CheckCacheRepoPort,
        fias_client: FiasClient,
        *,
        fias_mode: str,
        cache_version: str,
        settings: Settings | None = None,
    ):
        """Create use-case instance with required ports."""

        self._address_risk_check_use_case = address_risk_check_use_case
        self._check_results_repo = check_results_repo
        self._check_cache_repo = check_cache_repo
        self._fias_client = fias_client
        self._fias_mode = fias_mode
        self._cache_version = cache_version
        self._settings = settings

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
                extras,
            ) = await self._process_address(
                query.query,
            )

        elif query.type is QueryType.url:
            (
                snapshot,
                check_id,
                risk_result,
                signals,
                extras,
            ) = await self._process_url(
                query.query,
            )

        else:
            signals = (
                build_single_signal(
                    code='query_type_not_supported',
                    evidence=('rule:query_type_not_supported',),
                ),
            )
            extras = {}

        if snapshot is not None:
            risk_card = snapshot.risk_card
            normalized_address = snapshot.normalized_address
            fias_payload = snapshot.fias_payload
        elif risk_result is not None:
            risk_card = risk_result.risk_card
            normalized_address = risk_result.normalized_address
            fias_payload = None
        else:
            risk_card = build_risk_card(signals)
            normalized_address = None
            fias_payload = None

        listing_payload = extras.get('listing')
        listing_error = extras.get('listing_error')
        sources_payload = extras.get('sources')
        if snapshot is not None:
            listing_payload = snapshot.listing_payload or listing_payload
            listing_error = snapshot.listing_error or listing_error
            sources_payload = snapshot.sources_payload or sources_payload

        return self._build_response(
            risk_card,
            normalized_address,
            check_id,
            fias_payload,
            listing_payload,
            listing_error,
            sources_payload,
        )

    async def _process_address(self, text: str) -> tuple[
        CheckResultSnapshot | None,
        UUID | None,
        AddressRiskCheckResult | None,
        tuple[RiskSignal, ...],
        dict[str, Any],
    ]:
        """Обработать адресный запрос с учётом кэша."""

        return await process_address(
            text=text,
            fetch_fias_data=self._fetch_fias_data,
            run_address_risk_check=self._run_address_risk_check,
            store_check_result=self._store_check_result,
            check_cache_repo=self._check_cache_repo,
            check_results_repo=self._check_results_repo,
            fias_mode=self._fias_mode,
            cache_version=self._cache_version,
        )

    async def _process_url(self, url_text: str) -> tuple[
        CheckResultSnapshot | None,
        UUID | None,
        AddressRiskCheckResult | None,
        tuple[RiskSignal, ...],
        dict[str, Any],
    ]:
        """Обработать запрос URL и учесть кэш."""

        from checks.infrastructure import listing_resolver_container

        listing_resolver_factory = get_listing_resolver_use_case
        if (
            getattr(listing_resolver_factory, '__module__', '')
            == 'checks.infrastructure.listing_resolver_container'
        ):
            listing_resolver_factory = (
                listing_resolver_container.get_listing_resolver_use_case
            )

        listing_resolver_uc = listing_resolver_factory()

        return await process_url(
            url_text=url_text,
            listing_resolver_uc=listing_resolver_uc,
            fetch_fias_data=self._fetch_fias_data,
            run_address_risk_check=self._run_address_risk_check,
            store_check_result=self._store_check_result,
            check_cache_repo=self._check_cache_repo,
            check_results_repo=self._check_results_repo,
            fias_mode=self._fias_mode,
            cache_version=self._cache_version,
        )

    @staticmethod
    def _build_response(
        risk_card: RiskCard,
        normalized_address: AddressNormalized | None,
        check_id: UUID | None,
        fias_payload: dict[str, Any] | None,
        listing_payload: dict[str, Any] | None,
        listing_error: str | None,
        sources_payload: dict[str, Any] | None,
    ) -> dict[str, Any]:
        """Сформировать ответ API из риск-карты и адреса."""

        return build_response(
            risk_card=risk_card,
            normalized_address=normalized_address,
            check_id=check_id,
            fias_payload=fias_payload,
            listing_payload=listing_payload,
            listing_error=listing_error,
            sources_payload=sources_payload,
        )

    async def _run_address_risk_check(
        self,
        raw_address: str,
    ) -> tuple[AddressRiskCheckResult, tuple[RiskSignal, ...]]:
        """Запустить сценарий риск-проверки адреса."""

        normalized_raw = normalize_address_raw(raw_address)
        result = await self._address_risk_check_use_case.execute(
            normalized_raw,
        )
        return result, tuple(result.signals)

    async def _store_check_result(
        self,
        raw_input: str,
        result: AddressRiskCheckResult,
        *,
        kind: str,
        fias_payload: dict[str, Any] | None = None,
        fias_debug_raw: dict[str, Any] | None = None,
        listing_payload: dict[str, Any] | None = None,
        listing_error: str | None = None,
        sources_payload: dict[str, Any] | None = None,
    ) -> tuple[CheckResultSnapshot, UUID]:
        """Сохранить результирующий снимок проверки."""

        return await store_check_result(
            repo=self._check_results_repo,
            raw_input=raw_input,
            result=result,
            kind=kind,
            fias_payload=fias_payload,
            fias_debug_raw=fias_debug_raw,
            listing_payload=listing_payload,
            listing_error=listing_error,
            sources_payload=sources_payload,
        )

    async def _fetch_fias_data(
        self,
        query: str,
    ) -> tuple[
        dict[str, Any] | None,
        dict[str, Any] | None,
        RosreestrHouseNormalized | None,
        dict[str, Any] | None,
        GisGkhHouseNormalized | None,
        dict[str, Any] | None,
        dict[str, Any] | None,
        list[RiskSignal],
    ]:
        """Получить нормализацию из ФИАС и Росреестра."""

        return await fetch_fias_data(
            fias_client=self._fias_client,
            fias_mode=self._fias_mode,
            query=query,
            settings=self._settings,
        )

    async def _build_rosreestr_payload(
        self,
        target_number: str | None,
    ) -> tuple[dict[str, Any] | None, RosreestrHouseNormalized | None]:
        """Получить данные Росреестра и собрать payload."""

        if not self._settings:
            return None, None

        return await build_rosreestr_payload(
            settings=self._settings,
            target_number=target_number,
        )

    async def _build_gis_gkh_payload(
        self,
        *,
        target_number: str | None,
        region_code: str | None,
        house_payload: dict[str, Any] | None,
    ) -> tuple[dict[str, Any] | None, GisGkhHouseNormalized | None]:
        """Получить данные GIS ЖКХ и собрать payload."""

        if not self._settings:
            return None, None
        return await build_gis_gkh_payload(
            settings=self._settings,
            target_number=target_number,
            region_code=region_code,
            house_payload=house_payload,
        )
