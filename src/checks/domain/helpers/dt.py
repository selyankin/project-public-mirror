from datetime import UTC, datetime

from src.checks.domain.exceptions.domain import DomainValidationError


def utcnow() -> datetime:
    """Return timezone-aware UTC timestamp."""
    return datetime.now(UTC)


def ensure_tzaware(value: datetime | None) -> None:
    """Ensure provided datetime is timezone-aware."""
    if (
        not value
        or value.tzinfo is None
        or value.tzinfo.utcoffset(value) is None
    ):
        raise DomainValidationError('Datetime must be timezone-aware.')
