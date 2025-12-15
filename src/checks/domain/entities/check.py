"""Entities for the Check bounded context."""

from __future__ import annotations

from datetime import datetime
from typing import Any
from uuid import uuid4

from src.checks.domain.constants.enums.domain import CheckStatus, QueryType
from src.checks.domain.exceptions.domain import DomainValidationError
from src.checks.domain.helpers.dt import ensure_tzaware, utcnow


class CheckId:
    """Identifier value object for Check aggregate."""

    __slots__ = ("value",)

    def __init__(self, value: str | None = None):
        """Constructor"""

        candidate = value or uuid4().hex
        if not candidate:
            raise DomainValidationError("CheckId cannot be empty.")

        if len(candidate) > 64:
            raise DomainValidationError("CheckId is too long.")

        self.value = candidate

    def __str__(self) -> str:
        return self.value

    def __eq__(self, other: Any) -> bool:
        if not isinstance(other, CheckId):
            return NotImplemented
        return self.value == other.value

    def __hash__(self) -> int:
        return hash(self.value)


class Check:
    """Aggregate root representing a single check."""

    __slots__ = (
        "id",
        "user_id",
        "object_id",
        "query_type",
        "raw_query",
        "job_id",
        "report_id",
        "status",
        "created_at",
        "updated_at",
        "error_code",
        "error_message",
    )

    def __init__(self, check_data: dict):
        """Constructor"""

        self.id: CheckId = check_data.get("id") or CheckId()
        self.user_id: str | None = check_data.get("user_id")
        self.object_id: str | None = check_data.get("object_id")
        self.query_type: QueryType | None = check_data.get("query_type")
        self.raw_query: str | None = self._validate_raw_query(
            check_data.get("raw_query")
        )
        self.job_id: str | None = check_data.get("job_id")
        self.report_id: str | None = check_data.get("report_id")
        self.status: CheckStatus | None = check_data.get("status")
        self.created_at: datetime | None = check_data.get("created_at")
        self.updated_at: datetime | None = check_data.get("updated_at")
        self.error_code: str | None = check_data.get("error_code")
        self.error_message: str | None = check_data.get("error_message")

        self._validate_timestamps()
        self._validate_error_state()

    def _validate_raw_query(self, value: str | None) -> str:
        if not isinstance(value, str):
            raise DomainValidationError("raw_query must be a string.")

        trimmed = value.strip()
        if not trimmed:
            raise DomainValidationError("raw_query cannot be empty.")

        if len(trimmed) > 2000:
            raise DomainValidationError("raw_query is too long.")

        return trimmed

    def _validate_timestamps(self) -> None:
        ensure_tzaware(self.created_at)
        ensure_tzaware(self.updated_at)

        if (
            self.created_at
            and self.updated_at
            and self.updated_at < self.created_at
        ):
            raise DomainValidationError(
                "updated_at cannot be earlier than created_at.",
            )

    def _validate_error_state(self) -> None:
        if self.status == CheckStatus.failed:
            if not (self.error_message and self.error_message.strip()):
                raise DomainValidationError(
                    "Failed checks must contain an error message.",
                )
        elif self.error_message is not None or self.error_code is not None:
            raise DomainValidationError(
                "Only failed checks may contain error details.",
            )

    def touch(self) -> None:
        self.updated_at = utcnow()

    def _clear_error(self) -> None:
        self.error_code = None
        self.error_message = None

    def mark_queued(self) -> None:
        self.status = CheckStatus.queued
        self._clear_error()
        self.touch()

    def mark_building(self) -> None:
        self.status = CheckStatus.building
        self._clear_error()
        self.touch()

    def mark_ready(self, report_id: str | None = None) -> None:
        self.status = CheckStatus.ready
        self._clear_error()
        if report_id is not None:
            self.report_id = report_id
        self.touch()

    def mark_failed(self, message: str, code: str | None = None) -> None:
        if not message or not message.strip():
            raise DomainValidationError("Failure message cannot be empty.")

        self.status = CheckStatus.failed
        self.error_message = message
        self.error_code = code
        self.touch()

    def validate_query_type(self) -> None:
        if self.query_type and self.query_type not in (
            QueryType.url,
            QueryType.address,
        ):
            raise DomainValidationError(
                f"Query type {self.query_type.value} is not supported in MVP.",
            )
