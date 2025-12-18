from uuid import UUID

from pydantic import BaseModel


class RiskSignalOut(BaseModel):
    """Serialized risk signal representation."""

    code: str
    title: str
    description: str
    severity: int
    evidence_refs: list[str]


class FiasNormalizedOut(BaseModel):
    """Сериализованная нормализация адреса из ФИАС."""

    source_query: str
    normalized: str
    fias_id: str | None = None
    confidence: float | None = None


class RiskCardOut(BaseModel):
    """Сериализованный RiskCard."""

    score: int
    level: str
    summary: str
    signals: list[RiskSignalOut]
    address_confidence: str | None = None
    address_source: str | None = None
    check_id: UUID | None = None
    fias: FiasNormalizedOut | None = None
