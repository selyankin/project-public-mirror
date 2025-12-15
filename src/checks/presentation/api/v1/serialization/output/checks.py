from pydantic import BaseModel


class RiskSignalOut(BaseModel):
    """Serialized risk signal representation."""

    code: str
    title: str
    description: str
    severity: int
    evidence_refs: list[str]


class RiskCardOut(BaseModel):
    """Serialized risk card representation."""

    score: int
    level: str
    summary: str
    signals: list[RiskSignalOut]
