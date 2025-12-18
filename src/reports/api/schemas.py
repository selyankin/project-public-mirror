"""Pydantic-схемы для отчётов."""

from __future__ import annotations

from datetime import datetime
from uuid import UUID

from pydantic import BaseModel, Field


class CreateReportIn(BaseModel):
    """Запрос на создание отчёта."""

    check_id: UUID
    modules: list[str] = Field(default_factory=list)


class CreateReportOut(BaseModel):
    """Ответ при запуске генерации отчёта."""

    report_id: UUID
    status: str


class ReportPayloadAddressOut(BaseModel):
    raw: str | None
    normalized: str
    confidence: str | None
    source: str | None


class ReportPayloadRiskOut(BaseModel):
    score: int
    level: str
    summary: str


class ReportPayloadSignalOut(BaseModel):
    code: str
    title: str
    description: str
    severity: int


class ReportPayloadMetaOut(BaseModel):
    check_id: UUID
    generated_at: datetime


class ReportPayloadOut(BaseModel):
    title: str
    summary: str
    address: ReportPayloadAddressOut
    risk: ReportPayloadRiskOut
    signals: list[ReportPayloadSignalOut]
    disclaimers: list[str]
    generated_from: ReportPayloadMetaOut


class ReportOut(BaseModel):
    """Полный ответ содержащий отчёт."""

    report_id: UUID
    check_id: UUID
    status: str
    created_at: datetime
    modules: list[str]
    payload: ReportPayloadOut
