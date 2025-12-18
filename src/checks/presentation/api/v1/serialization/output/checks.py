from uuid import UUID

from pydantic import BaseModel


class RiskSignalOut(BaseModel):
    """Serialized risk signal representation."""

    code: str
    title: str
    description: str
    severity: int
    evidence_refs: list[str]


class RiskCardOut(BaseModel):
    """Сериализованный RiskCard."""

    score: int
    level: str
    summary: str
    signals: list[RiskSignalOut]
    address_confidence: str | None = None
    address_source: str | None = None
    check_id: UUID | None = None
