"""Снимок результата проверки адреса."""

from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime
from typing import Any

from checks.domain.value_objects.address import AddressNormalized
from risks.domain.entities.risk_card import RiskCard, RiskSignal

CHECK_RESULT_SCHEMA_VERSION = 2


@dataclass(slots=True)
class CheckResultSnapshot:
    """Содержит данные проверки для повторного использования."""

    raw_input: str
    normalized_address: AddressNormalized
    signals: list[RiskSignal]
    risk_card: RiskCard
    created_at: datetime
    kind: str = 'address'
    schema_version: int = CHECK_RESULT_SCHEMA_VERSION
    fias_payload: dict[str, Any] | None = None
    fias_debug_raw: dict[str, Any] | None = None
