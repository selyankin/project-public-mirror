"""Основные сценарии обработки адреса и URL."""

from __future__ import annotations

from collections.abc import Awaitable, Callable
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
)
from checks.application.use_cases.check_address_cache import (
    build_cache_key,
    get_cached_snapshot,
)
from checks.application.use_cases.check_address_listing import (
    try_resolve_listing,
)
from checks.application.use_cases.check_address_payloads import (
    build_sources_payload,
)
from checks.application.use_cases.check_address_signals import (
    apply_gis_gkh_signals,
    apply_rosreestr_signals,
    build_single_signal,
    merge_signals,
    sanitize_input_value,
)
from checks.domain.constants.enums.domain import QueryType
from checks.domain.entities.check_result import CheckResultSnapshot
from checks.domain.helpers.address_heuristics import is_address_like
from checks.domain.value_objects.address import normalize_address_raw
from checks.domain.value_objects.query import CheckQuery
from checks.domain.value_objects.url import UrlRaw
from risks.application.scoring import build_risk_card
from risks.domain.entities.risk_card import RiskSignal

FetchFiasData = Callable[
    [str],
    Awaitable[
        tuple[
            dict[str, Any] | None,
            dict[str, Any] | None,
            Any | None,
            dict[str, Any] | None,
            Any | None,
            dict[str, Any] | None,
        ]
    ],
]
RunRiskCheck = Callable[
    [str],
    Awaitable[tuple[AddressRiskCheckResult, tuple[RiskSignal, ...]]],
]
StoreResult = Callable[
    ...,
    Awaitable[tuple[CheckResultSnapshot, UUID]],
]


async def process_address(
    *,
    text: str,
    fetch_fias_data: FetchFiasData,
    run_address_risk_check: RunRiskCheck,
    store_check_result: StoreResult,
    check_cache_repo: CheckCacheRepoPort,
    check_results_repo: CheckResultsRepoPort,
    fias_mode: str,
    cache_version: str,
) -> tuple[
    CheckResultSnapshot | None,
    UUID | None,
    AddressRiskCheckResult | None,
    tuple[RiskSignal, ...],
    dict[str, Any],
]:
    """Обработать адресный запрос с учётом кэша."""

    if not is_address_like(text):
        signals = (
            build_single_signal(
                code='query_not_address_like',
                evidence=('heuristic:address_like',),
            ),
        )
        return None, None, None, signals, {}

    (
        fias_payload,
        fias_debug_raw,
        rosreestr_house,
        rosreestr_payload,
        gis_gkh_house,
        gis_gkh_payload,
        kad_arbitr_payload,
        kad_arbitr_signals,
    ) = await fetch_fias_data(text)

    apply_rosreestr_signals(
        rosreestr_payload=rosreestr_payload,
        house=rosreestr_house,
        listing_payload=None,
    )
    extra_signals = apply_gis_gkh_signals(
        gis_gkh_payload=gis_gkh_payload,
        house=gis_gkh_house,
        listing_payload=None,
    )
    extra_signals = tuple(extra_signals) + tuple(kad_arbitr_signals)
    sources_payload = build_sources_payload(
        rosreestr_payload=rosreestr_payload,
        gis_gkh_payload=gis_gkh_payload,
        kad_arbitr_payload=kad_arbitr_payload,
    )
    extras: dict[str, Any] = {}
    if sources_payload:
        extras['sources'] = sources_payload

    normalized_input = normalize_address_raw(text).value
    cache_query = CheckQuery(
        {'type': QueryType.address.value, 'query': normalized_input},
    )
    cache_key = build_cache_key(
        query=cache_query,
        cache_version=cache_version,
        fias_mode=fias_mode,
    )
    cached_snapshot, cached_id = await get_cached_snapshot(
        cache_repo=check_cache_repo,
        results_repo=check_results_repo,
        key=cache_key,
    )
    if cached_snapshot is not None and cached_id is not None:
        return cached_snapshot, cached_id, None, (), extras

    risk_result, _ = await run_address_risk_check(text)
    merged_signals = merge_signals(
        base=tuple(risk_result.signals),
        extra=extra_signals,
    )
    if merged_signals != tuple(risk_result.signals):
        risk_result.signals = list(merged_signals)
        risk_result.risk_card = build_risk_card(merged_signals)

    snapshot, check_id = await store_check_result(
        raw_input=normalized_input,
        result=risk_result,
        kind='address',
        fias_payload=fias_payload,
        fias_debug_raw=fias_debug_raw,
        listing_payload=None,
        listing_error=None,
        sources_payload=sources_payload,
    )
    await check_cache_repo.set(cache_key, check_id)
    return snapshot, check_id, risk_result, merged_signals, extras


async def process_url(
    *,
    url_text: str,
    listing_resolver_uc: Any,
    fetch_fias_data: FetchFiasData,
    run_address_risk_check: RunRiskCheck,
    store_check_result: StoreResult,
    check_cache_repo: CheckCacheRepoPort,
    check_results_repo: CheckResultsRepoPort,
    fias_mode: str,
    cache_version: str,
) -> tuple[
    CheckResultSnapshot | None,
    UUID | None,
    AddressRiskCheckResult | None,
    tuple[RiskSignal, ...],
    dict[str, Any],
]:
    """Обработать запрос URL и учесть кэш."""

    normalized_input = sanitize_input_value(url_text)
    cache_query = CheckQuery(
        {'type': QueryType.url.value, 'query': normalized_input},
    )
    cache_key = build_cache_key(
        query=cache_query,
        cache_version=cache_version,
        fias_mode=fias_mode,
    )
    cached_snapshot, cached_id = await get_cached_snapshot(
        cache_repo=check_cache_repo,
        results_repo=check_results_repo,
        key=cache_key,
    )
    if cached_snapshot is not None and cached_id is not None:
        return cached_snapshot, cached_id, None, (), {}

    url_vo = UrlRaw(url_text)
    extracted = extract_address_from_url(url_vo)
    if extracted and is_address_like(extracted):
        normalized_address_input = normalize_address_raw(extracted).value
        (
            fias_payload,
            fias_debug_raw,
            rosreestr_house,
            rosreestr_payload,
            gis_gkh_house,
            gis_gkh_payload,
            kad_arbitr_payload,
            kad_arbitr_signals,
        ) = await fetch_fias_data(extracted)

        apply_rosreestr_signals(
            rosreestr_payload=rosreestr_payload,
            house=rosreestr_house,
            listing_payload=None,
        )
        extra_signals = apply_gis_gkh_signals(
            gis_gkh_payload=gis_gkh_payload,
            house=gis_gkh_house,
            listing_payload=None,
        )
        extra_signals = tuple(extra_signals) + tuple(kad_arbitr_signals)
        sources_payload = build_sources_payload(
            rosreestr_payload=rosreestr_payload,
            gis_gkh_payload=gis_gkh_payload,
            kad_arbitr_payload=kad_arbitr_payload,
        )
        extras: dict[str, Any] = {}
        if sources_payload:
            extras['sources'] = sources_payload
        risk_result, _ = await run_address_risk_check(extracted)
        merged_signals = merge_signals(
            base=tuple(risk_result.signals),
            extra=extra_signals,
        )
        if merged_signals != tuple(risk_result.signals):
            risk_result.signals = list(merged_signals)
            risk_result.risk_card = build_risk_card(merged_signals)

        snapshot, check_id = await store_check_result(
            raw_input=normalized_address_input,
            result=risk_result,
            kind='url',
            fias_payload=fias_payload,
            fias_debug_raw=fias_debug_raw,
            listing_payload=None,
            listing_error=None,
            sources_payload=sources_payload,
        )
        await check_cache_repo.set(cache_key, check_id)
        return snapshot, check_id, risk_result, merged_signals, extras

    listing_result, listing_error = await try_resolve_listing(
        listing_resolver_uc=listing_resolver_uc,
        url=url_vo,
    )
    extras: dict[str, Any] = {}
    if listing_result:
        listing_address, listing_payload = listing_result
        normalized_address_input = normalize_address_raw(
            listing_address,
        ).value
        (
            fias_payload,
            fias_debug_raw,
            rosreestr_house,
            rosreestr_payload,
            gis_gkh_house,
            gis_gkh_payload,
            kad_arbitr_payload,
            kad_arbitr_signals,
        ) = await fetch_fias_data(listing_address)

        apply_rosreestr_signals(
            rosreestr_payload=rosreestr_payload,
            house=rosreestr_house,
            listing_payload=listing_payload,
        )
        extra_signals = apply_gis_gkh_signals(
            gis_gkh_payload=gis_gkh_payload,
            house=gis_gkh_house,
            listing_payload=listing_payload,
        )
        extra_signals = tuple(extra_signals) + tuple(kad_arbitr_signals)
        sources_payload = build_sources_payload(
            rosreestr_payload=rosreestr_payload,
            gis_gkh_payload=gis_gkh_payload,
            kad_arbitr_payload=kad_arbitr_payload,
        )
        risk_result, _ = await run_address_risk_check(listing_address)
        merged_signals = merge_signals(
            base=tuple(risk_result.signals),
            extra=extra_signals,
        )
        if merged_signals != tuple(risk_result.signals):
            risk_result.signals = list(merged_signals)
            risk_result.risk_card = build_risk_card(merged_signals)

        snapshot, check_id = await store_check_result(
            raw_input=normalized_address_input,
            result=risk_result,
            kind='url',
            fias_payload=fias_payload,
            fias_debug_raw=fias_debug_raw,
            listing_payload=listing_payload,
            listing_error=None,
            sources_payload=sources_payload,
        )
        extras['listing'] = listing_payload
        if sources_payload:
            extras['sources'] = sources_payload
        await check_cache_repo.set(cache_key, check_id)
        return snapshot, check_id, risk_result, merged_signals, extras

    if listing_error:
        extras['listing_error'] = listing_error

    signals = (
        build_single_signal(
            code='url_not_supported_yet',
            evidence=('rule:url_not_supported',),
        ),
    )
    return None, None, None, signals, extras
