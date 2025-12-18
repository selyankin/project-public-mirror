"""Снимок результата проверки адреса."""

from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime

from checks.domain.value_objects.address import AddressNormalized
from risks.domain.entities.risk_card import RiskCard, RiskSignal


@dataclass(slots=True)
class CheckResultSnapshot:
    """Содержит данные проверки для повторного использования."""

    raw_input: str
    normalized_address: AddressNormalized
    signals: list[RiskSignal]
    risk_card: RiskCard
    created_at: datetime
    kind: str = 'address'
    schema_version: int = 1
