"""Pydantic-схемы для отчётов."""

from __future__ import annotations

from datetime import datetime
from typing import Any
from uuid import UUID

from pydantic import BaseModel, Field

from reports.domain.modules.catalog import DEFAULT_MODULES


class CreateReportIn(BaseModel):
    """Запрос на создание отчёта."""

    check_id: UUID
    modules: list[str] = Field(default_factory=lambda: list(DEFAULT_MODULES))


class CreateReportOut(BaseModel):
    """Ответ при запуске генерации отчёта."""

    report_id: UUID
    status: str


class ReportPayloadMetaOut(BaseModel):
    check_id: UUID
    generated_at: datetime
    schema_version: int
    modules: list[str]
    disclaimers: list[str]


class ReportPayloadOut(BaseModel):
    meta: ReportPayloadMetaOut
    sections: dict[str, Any]


class ReportOut(BaseModel):
    """Полный ответ содержащий отчёт."""

    report_id: UUID
    check_id: UUID
    status: str
    created_at: datetime
    modules: list[str]
    payload: ReportPayloadOut
