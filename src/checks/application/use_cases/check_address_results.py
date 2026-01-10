"""Сборка результата проверки и ответов."""

from __future__ import annotations

from datetime import UTC, datetime
from typing import Any
from uuid import UUID

from checks.application.ports.checks import CheckResultsRepoPort
from checks.application.use_cases.address_risk_check import (
    AddressRiskCheckResult,
)
from checks.domain.entities.check_result import CheckResultSnapshot
from checks.domain.value_objects.address import AddressNormalized
from risks.domain.entities.risk_card import RiskCard


def build_response(
    *,
    risk_card: RiskCard,
    normalized_address: AddressNormalized | None,
    check_id: UUID | None,
    fias_payload: dict[str, Any] | None,
    listing_payload: dict[str, Any] | None,
    listing_error: str | None,
    sources_payload: dict[str, Any] | None,
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
    if sources_payload:
        result['sources'] = sources_payload

    return result


async def store_check_result(
    *,
    repo: CheckResultsRepoPort,
    raw_input: str,
    result: AddressRiskCheckResult,
    kind: str,
    fias_payload: dict[str, Any] | None = None,
    fias_debug_raw: dict[str, Any] | None = None,
    listing_payload: dict[str, Any] | None = None,
    listing_error: str | None = None,
    sources_payload: dict[str, Any] | None = None,
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
        sources_payload=sources_payload,
    )
    check_id = await repo.save(snapshot)
    return snapshot, check_id
