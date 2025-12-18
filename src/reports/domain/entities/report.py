"""Доменные сущности отчёта по проверке адреса."""

from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime
from typing import Literal
from uuid import UUID


@dataclass(slots=True)
class ReportPayloadAddress:
    """Адресная часть отчёта."""

    raw: str | None
    normalized: str
    confidence: str | None
    source: str | None


@dataclass(slots=True)
class ReportPayloadRisk:
    """Сводка по риску."""

    score: int
    level: str
    summary: str


@dataclass(slots=True)
class ReportPayloadSignal:
    """Описание сигнала внутри отчёта."""

    code: str
    title: str
    description: str
    severity: int


@dataclass(slots=True)
class ReportPayloadMeta:
    """Метаданные происхождения отчёта."""

    check_id: UUID
    generated_at: datetime


@dataclass(slots=True)
class ReportPayload:
    """Полезная нагрузка отчёта для клиента."""

    title: str
    summary: str
    address: ReportPayloadAddress
    risk: ReportPayloadRisk
    signals: list[ReportPayloadSignal]
    disclaimers: list[str]
    generated_from: ReportPayloadMeta


@dataclass(slots=True)
class Report:
    """Отчёт по результатам проверки."""

    id: UUID
    check_id: UUID
    created_at: datetime
    status: Literal['ready']
    modules: list[str]
    payload: ReportPayload
