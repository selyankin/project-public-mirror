from enum import IntEnum, StrEnum


class RiskLevel(StrEnum):
    """Overall risk level."""

    low = 'low'
    medium = 'medium'
    high = 'high'


class SignalSeverity(IntEnum):
    """Severity scale for individual signals."""

    info = 1
    low = 2
    medium = 3
    high = 4
    critical = 5
