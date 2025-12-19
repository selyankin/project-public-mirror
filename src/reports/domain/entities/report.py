"""Доменные сущности отчёта по проверке адреса."""

from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime
from typing import Any, Literal
from uuid import UUID


@dataclass(slots=True)
class ReportPayloadMeta:
    """Метаданные и служебная информация отчёта."""

    check_id: UUID
    generated_at: datetime
    schema_version: int
    modules: list[str]
    disclaimers: list[str]


@dataclass(slots=True)
class ReportPayload:
    """Полезная нагрузка отчёта в виде модульных секций."""

    meta: ReportPayloadMeta
    sections: dict[str, Any]


@dataclass(slots=True)
class Report:
    """Отчёт по результатам проверки."""

    id: UUID
    check_id: UUID
    created_at: datetime
    status: Literal['ready']
    modules: list[str]
    payload: ReportPayload
