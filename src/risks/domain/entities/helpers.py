from risks.domain.constants.enums.risk import RiskLevel, SignalSeverity
from risks.domain.exceptions.risk import RiskDomainError


def ensure_non_empty_str(value: object, field: str, max_len: int) -> str:
    """Return a trimmed non-empty string bounded by max_len."""

    if not isinstance(value, str):
        raise RiskDomainError(f'{field} must be a string.')

    candidate = value.strip()
    if not candidate:
        raise RiskDomainError(f'{field} cannot be empty.')

    if len(candidate) > max_len:
        raise RiskDomainError(f'{field} length must be <= {max_len}.')

    return candidate


def coerce_risk_level(value: object) -> RiskLevel:
    """Convert raw input into a RiskLevel enum."""

    if isinstance(value, RiskLevel):
        return value

    if isinstance(value, str):
        key = value.strip().lower()
        if not key:
            raise RiskDomainError('Risk level cannot be empty.')
        try:
            return RiskLevel(key)
        except ValueError as exc:
            raise RiskDomainError(f'Unknown risk level: {value!r}') from exc

    raise RiskDomainError('Risk level must be a string or RiskLevel.')


def coerce_severity(value: object) -> SignalSeverity:
    """Convert raw input into a SignalSeverity enum."""

    if isinstance(value, SignalSeverity):
        return value

    if isinstance(value, int):
        try:
            return SignalSeverity(value)
        except ValueError as exc:
            raise RiskDomainError(f'Unknown severity: {value}') from exc

    if isinstance(value, str):
        candidate = value.strip().lower()
        if not candidate:
            raise RiskDomainError('Severity cannot be empty.')
        if candidate.isdigit():
            return coerce_severity(int(candidate))
        try:
            return SignalSeverity[candidate]
        except KeyError as exc:
            raise RiskDomainError(f'Unknown severity: {value!r}') from exc

    raise RiskDomainError('Severity must be str, int, or SignalSeverity.')


def level_from_score(score: int) -> RiskLevel:
    """Map numeric scores to risk levels."""

    if not isinstance(score, int):
        raise RiskDomainError('Score must be an integer.')

    if score < 0 or score > 100:
        raise RiskDomainError('Score must be between 0 and 100.')

    if score <= 29:
        return RiskLevel.low

    if score <= 69:
        return RiskLevel.medium

    return RiskLevel.high
