"""Use-case проверки адресов и URL."""

from __future__ import annotations

import asyncio
import logging
from dataclasses import asdict
from datetime import UTC, date, datetime
from typing import Any
from uuid import UUID

from checks.application.helpers.url_extraction import (
    extract_address_from_url,
)
from checks.application.ports.checks import (
    CheckCacheRepoPort,
    CheckResultsRepoPort,
)
from checks.application.ports.fias_client import FiasClient, NormalizedAddress
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
from checks.infrastructure.listing_resolver_container import (
    get_listing_resolver_use_case,
)
from checks.infrastructure.rosreestr_resolver_container import (
    get_rosreestr_resolver_use_case,
)
from risks.application.scoring import build_risk_card
from risks.domain.entities.risk_card import RiskCard, RiskSignal
from risks.domain.signals_catalog import get_signal_definition
from shared.domain.entities import HouseKey
from shared.kernel.settings import Settings
from sources.domain.entities import ListingNormalized
from sources.domain.exceptions import (
    ListingFetchError,
    ListingNotSupportedError,
    ListingParseError,
)
from sources.rosreestr.models import RosreestrHouseNormalized
from sources.rosreestr.signals import build_rosreestr_signals

logger = logging.getLogger(__name__)


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

        extras: dict[str, Any] = {}

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
                self._build_single_signal(
                    'query_type_not_supported',
                    ('rule:query_type_not_supported',),
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
        if snapshot is not None:
            listing_payload = snapshot.listing_payload or listing_payload
            listing_error = snapshot.listing_error or listing_error

        return self._build_response(
            risk_card,
            normalized_address,
            check_id,
            fias_payload,
            listing_payload,
            listing_error,
        )

    async def _process_address(self, text: str) -> tuple[
        CheckResultSnapshot | None,
        UUID | None,
        AddressRiskCheckResult | None,
        tuple[RiskSignal, ...],
        dict[str, Any],
    ]:
        """Обработать адресный запрос с учётом кэша."""

        if not is_address_like(text):
            signals = (
                self._build_single_signal(
                    'query_not_address_like',
                    ('heuristic:address_like',),
                ),
            )
            return None, None, None, signals, {}

        fias_payload, fias_debug_raw, rosreestr_house = (
            await self._fetch_fias_data(text)
        )
        self._apply_rosreestr_signals(fias_payload, rosreestr_house, None)

        normalized_input = normalize_address_raw(text).value
        cache_key = self._build_cache_key(
            input_kind='address',
            input_value=normalized_input,
        )
        cached = await self._get_cached_snapshot(cache_key)
        if cached:
            return cached[0], cached[1], None, (), {}

        risk_result, signals = await self._run_address_risk_check(text)
        snapshot, check_id = await self._store_check_result(
            normalized_input,
            risk_result,
            kind='address',
            fias_payload=fias_payload,
            fias_debug_raw=fias_debug_raw,
        )
        await self._check_cache_repo.set(cache_key, check_id)
        return snapshot, check_id, risk_result, signals, {}

    async def _process_url(self, url_text: str) -> tuple[
        CheckResultSnapshot | None,
        UUID | None,
        AddressRiskCheckResult | None,
        tuple[RiskSignal, ...],
        dict[str, Any],
    ]:
        """Обработать запрос URL и учесть кэш."""

        normalized_input = self._sanitize_input_value(url_text)
        cache_key = self._build_cache_key(
            input_kind='url',
            input_value=normalized_input,
        )
        cached = await self._get_cached_snapshot(cache_key)
        if cached:
            return cached[0], cached[1], None, (), {}

        url_vo = UrlRaw(url_text)
        extracted = extract_address_from_url(url_vo)
        if extracted and is_address_like(extracted):
            normalized_address_input = normalize_address_raw(extracted).value
            fias_payload, fias_debug_raw, rosreestr_house = (
                await self._fetch_fias_data(extracted)
            )
            self._apply_rosreestr_signals(
                fias_payload,
                rosreestr_house,
                None,
            )
            risk_result, signals = await self._run_address_risk_check(
                extracted,
            )
            snapshot, check_id = await self._store_check_result(
                normalized_address_input,
                risk_result,
                kind='url',
                fias_payload=fias_payload,
                fias_debug_raw=fias_debug_raw,
            )
            await self._check_cache_repo.set(cache_key, check_id)
            return snapshot, check_id, risk_result, signals, {}

        listing_result, listing_error = await self._try_resolve_listing(
            url_text,
        )
        extras: dict[str, Any] = {}
        if listing_result:
            listing_address, listing_payload = listing_result
            normalized_address_input = normalize_address_raw(
                listing_address,
            ).value
            fias_payload, fias_debug_raw, rosreestr_house = (
                await self._fetch_fias_data(listing_address)
            )
            self._apply_rosreestr_signals(
                fias_payload,
                rosreestr_house,
                listing_payload,
            )
            risk_result, signals = await self._run_address_risk_check(
                listing_address,
            )
            snapshot, check_id = await self._store_check_result(
                normalized_address_input,
                risk_result,
                kind='url',
                fias_payload=fias_payload,
                fias_debug_raw=fias_debug_raw,
                listing_payload=listing_payload,
                listing_error=None,
            )
            extras['listing'] = listing_payload
            await self._check_cache_repo.set(cache_key, check_id)
            return snapshot, check_id, risk_result, signals, extras

        if listing_error:
            extras['listing_error'] = listing_error

        signals = (
            self._build_single_signal(
                'url_not_supported_yet',
                ('rule:url_not_supported',),
            ),
        )
        return None, None, None, signals, extras

    def _build_cache_key(
        self,
        *,
        input_kind: str,
        input_value: str,
    ) -> str:
        """Построить ключ кэша для проверки."""

        # TODO: включить нормализованный ответ ФИАС в ключ после
        #  стабилизации схемы внешнего API.
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

    async def _try_resolve_listing(
        self,
        url_text: str,
    ) -> tuple[tuple[str, dict[str, Any]] | None, str | None]:
        """Попробовать извлечь адрес из листинга."""

        resolver = get_listing_resolver_use_case()
        try:
            listing = await asyncio.to_thread(
                resolver.execute,
                url_text,
            )
        except ListingNotSupportedError as exc:
            logger.info('listing_not_supported url=%s error=%s', url_text, exc)
            return None, 'ListingNotSupportedError'
        except (ListingFetchError, ListingParseError) as exc:
            logger.info(
                'listing_resolver_failed url=%s error=%s', url_text, exc
            )
            return None, exc.__class__.__name__
        except Exception as exc:  # pragma: no cover
            logger.warning(
                'listing_resolver_unexpected_error url=%s error=%s',
                url_text,
                exc,
            )
            return None, 'UnexpectedError'

        if listing.address_text and is_address_like(listing.address_text):
            payload = self._listing_to_payload(listing)
            return (listing.address_text, payload), None

        return None, None

    @staticmethod
    def _build_response(
        risk_card: RiskCard,
        normalized_address: AddressNormalized | None,
        check_id: UUID | None,
        fias_payload: dict[str, Any] | None,
        listing_payload: dict[str, Any] | None,
        listing_error: str | None,
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
        if fias_payload:
            result['fias'] = fias_payload
        if listing_payload:
            result['listing'] = listing_payload
        if listing_error:
            result['listing_error'] = listing_error

        return result

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
    ) -> tuple[CheckResultSnapshot, UUID]:
        """Сохранить результирующий снимок проверки."""

        snapshot = CheckResultSnapshot(
            raw_input=raw_input,
            normalized_address=result.normalized_address,
            signals=list(result.signals),
            risk_card=result.risk_card,
            created_at=datetime.now(UTC),
            kind=kind,
            fias_payload=fias_payload,
            fias_debug_raw=fias_debug_raw,
            listing_payload=listing_payload,
            listing_error=listing_error,
        )
        check_id = await self._check_results_repo.save(snapshot)
        return snapshot, check_id

    async def _fetch_fias_data(
        self,
        query: str,
    ) -> tuple[
        dict[str, Any] | None,
        dict[str, Any] | None,
        RosreestrHouseNormalized | None,
    ]:
        """Получить нормализацию из ФИАС и Росреестра."""

        try:
            normalized = await self._fias_client.normalize_address(query)
        except Exception as exc:
            logger.warning(
                'fias_normalize_failed mode=%s query=%s error=%s',
                self._fias_mode,
                query[:80],
                exc,
            )
            return None, None, None

        if normalized is None:
            return None, None, None

        public_payload = {
            'source_query': normalized.source_query,
            'normalized': normalized.normalized,
            'fias_id': normalized.fias_id,
            'confidence': normalized.confidence,
        }
        house_payload = self._build_house_payload(normalized)
        if house_payload:
            public_payload['house'] = house_payload

        rosreestr_payload, rosreestr_house = (
            await self._build_rosreestr_payload(
                house_payload,
                normalized.cadastral_number,
            )
        )
        if rosreestr_payload:
            public_payload['rosreestr'] = rosreestr_payload

        return public_payload, normalized.raw, rosreestr_house

    @staticmethod
    def _build_house_payload(dto: NormalizedAddress) -> dict[str, Any] | None:
        """Собрать публичный payload идентификаторов дома."""

        try:
            house_key = HouseKey.build(
                fias_houseguid=dto.fias_houseguid,
                gar_house_id=dto.gar_house_id,
                gar_object_id=dto.gar_object_id,
            )
            house_key_value = house_key.value
        except ValueError:
            house_key_value = None

        payload: dict[str, Any] = {}
        if house_key_value:
            payload['house_key'] = house_key_value
        if dto.fias_houseguid:
            payload['fias_houseguid'] = dto.fias_houseguid
        if dto.fias_aoguid:
            payload['fias_aoguid'] = dto.fias_aoguid
        if dto.gar_house_id:
            payload['gar_house_id'] = dto.gar_house_id
        if dto.gar_object_id:
            payload['gar_object_id'] = dto.gar_object_id
        if dto.postal_code:
            payload['postal_code'] = dto.postal_code
        if dto.oktmo:
            payload['oktmo'] = dto.oktmo
        if dto.okato:
            payload['okato'] = dto.okato
        if dto.region_code:
            payload['region_code'] = dto.region_code
        if dto.cadastral_number:
            payload['cadastral_number'] = dto.cadastral_number
        if dto.status:
            payload['status'] = dto.status
        if dto.is_active is not None:
            payload['is_active'] = dto.is_active
        if dto.updated_at is not None:
            payload['updated_at'] = dto.updated_at.isoformat()

        return payload or None

    async def _build_rosreestr_payload(
        self,
        house_payload: dict[str, Any] | None,
        cadastral_number: str | None,
    ) -> tuple[dict[str, Any] | None, RosreestrHouseNormalized | None]:
        """Получить данные Росреестра и собрать payload."""

        if not self._settings:
            return None, None

        target_number = (
            house_payload.get('cadastral_number') if house_payload else None
        )
        if not target_number:
            target_number = cadastral_number

        if not target_number:
            return None, None

        resolver = get_rosreestr_resolver_use_case(self._settings)
        try:
            house = await asyncio.to_thread(
                resolver.execute,
                cadastral_number=target_number,
            )
        except Exception as exc:
            logger.info(
                'rosreestr_resolver_failed cadastral=%s error=%s',
                target_number,
                exc,
            )
            return (
                {
                    'found': False,
                    'house': None,
                    'error': exc.__class__.__name__,
                    'signals': [],
                },
                None,
            )

        if house is None:
            return (
                {
                    'found': False,
                    'house': None,
                    'error': None,
                    'signals': [],
                },
                None,
            )

        return (
            {
                'found': True,
                'house': self._rosreestr_house_to_payload(house),
                'error': None,
                'signals': [],
            },
            house,
        )

    def _apply_rosreestr_signals(
        self,
        fias_payload: dict[str, Any] | None,
        rosreestr_house: RosreestrHouseNormalized | None,
        listing_payload: dict[str, Any] | None,
    ) -> None:
        """Добавить сигналы Росреестра к payload."""

        if not fias_payload:
            return

        block = fias_payload.get('rosreestr')
        if not block:
            return

        listing_area = (
            listing_payload.get('area_total') if listing_payload else None
        )
        listing_floors = (
            listing_payload.get('floors_total') if listing_payload else None
        )
        if rosreestr_house is None:
            block.setdefault('signals', [])
            return

        signals = build_rosreestr_signals(
            rosreestr=rosreestr_house,
            listing_area_total=listing_area,
            listing_floors_total=listing_floors,
        )
        block['signals'] = [signal.to_dict() for signal in signals]

    @staticmethod
    def _rosreestr_house_to_payload(
        house: RosreestrHouseNormalized,
    ) -> dict[str, Any]:
        """Преобразовать доменную модель Росреестра к dict."""

        payload = asdict(house)
        for key, value in payload.items():
            if isinstance(value, date):
                payload[key] = value.isoformat()

        return payload

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

    @staticmethod
    def _listing_to_payload(listing: ListingNormalized) -> dict[str, Any]:
        """Сериализовать листинг для хранения."""

        return {
            'source': listing.source,
            'url': listing.url.value,
            'listing_id': listing.listing_id.value,
            'title': listing.title,
            'address_text': listing.address_text,
            'price': listing.price,
            'coords': {
                'lat': listing.coords_lat,
                'lon': listing.coords_lon,
            },
            'area_total': listing.area_total,
            'floors_total': listing.floors_total,
        }
