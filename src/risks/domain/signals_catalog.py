"""Catalog of risk signal definitions."""

from __future__ import annotations

from typing import Any

from src.risks.domain.constants.enums.risk import SignalSeverity
from src.risks.domain.exceptions.risk import RiskDomainError


class SignalDefinition:
    """Definition of a risk signal."""

    __slots__ = (
        "code",
        "title",
        "description",
        "severity",
    )

    def __init__(self, data: dict[str, Any]):
        """Create a signal definition from raw data."""

        if not isinstance(data, dict):
            raise RiskDomainError("SignalDefinition data must be a dict.")

        self.code = self._ensure_non_empty(data.get("code"), "code", 80)
        self.title = self._ensure_non_empty(data.get("title"), "title", 200)
        self.description = self._ensure_non_empty(
            data.get("description"),
            "description",
            2000,
        )
        self.severity = self._coerce_severity(data.get("severity"))

    @staticmethod
    def _ensure_non_empty(
        value: Any,
        field: str,
        max_len: int,
    ) -> str:
        if not isinstance(value, str):
            raise RiskDomainError(f"{field} must be a string.")

        trimmed = value.strip()
        if not trimmed:
            raise RiskDomainError(f"{field} cannot be empty.")

        if len(trimmed) > max_len:
            raise RiskDomainError(f"{field} length must be <= {max_len}.")

        return trimmed

    def _coerce_severity(self, value: Any) -> SignalSeverity:
        if isinstance(value, SignalSeverity):
            return value

        if isinstance(value, int):
            try:
                return SignalSeverity(value)
            except ValueError as exc:
                raise RiskDomainError(f"Unknown severity: {value}") from exc

        if isinstance(value, str):
            key = value.strip().lower()
            if not key:
                raise RiskDomainError("Severity cannot be empty.")

            if key.isdigit():
                return self._coerce_severity(int(key))

            try:
                return SignalSeverity[key]
            except KeyError as exc:
                raise RiskDomainError(f"Unknown severity: {value!r}") from exc

        raise RiskDomainError("Severity must be str, int, or SignalSeverity.")

    def to_dict(self) -> dict[str, Any]:
        """Serialize definition to a plain dict."""

        return {
            "code": self.code,
            "title": self.title,
            "description": self.description,
            "severity": int(self.severity),
        }
