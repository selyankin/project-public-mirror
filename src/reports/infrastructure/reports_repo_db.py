"""Репозиторий отчётов поверх async SQLAlchemy."""

from __future__ import annotations

from datetime import datetime
from typing import Any
from uuid import UUID

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker

from reports.application.ports.repos import ReportsRepoPort
from reports.domain.entities.report import (
    Report,
    ReportPayload,
    ReportPayloadMeta,
)
from shared.infra.db.models.report import ReportModel
from shared.kernel.db import session_scope


class ReportsRepoDb(ReportsRepoPort):
    """Сохраняет отчёты в таблице reports."""

    __slots__ = ('_session_factory',)

    def __init__(
        self,
        session_factory: async_sessionmaker[AsyncSession],
    ) -> None:
        """Запомнить фабрику сессий."""

        self._session_factory = session_factory

    async def save(self, report: Report) -> UUID:
        """Сохранить отчёт и вернуть его идентификатор."""

        payload = self._serialize_payload(report.payload)
        async with session_scope(self._session_factory) as session:
            model = ReportModel(
                id=report.id,
                created_at=report.created_at,
                check_id=report.check_id,
                status=report.status,
                modules=list(report.modules),
                payload=payload,
            )
            session.add(model)
            await session.flush()
            return model.id

    async def get(self, report_id: UUID) -> Report | None:
        """Вернуть отчёт по идентификатору."""

        async with session_scope(self._session_factory) as session:
            stmt = select(ReportModel).where(ReportModel.id == report_id)
            model = await session.scalar(stmt)
            if model is None:
                return None
            return self._deserialize_report(model)

    @staticmethod
    def _serialize_payload(payload: ReportPayload) -> dict[str, Any]:
        """Преобразовать доменный payload в JSON."""

        meta = payload.meta
        return {
            'meta': {
                'check_id': str(meta.check_id),
                'generated_at': meta.generated_at.isoformat(),
                'schema_version': meta.schema_version,
                'modules': list(meta.modules),
                'disclaimers': list(meta.disclaimers),
            },
            'sections': payload.sections,
        }

    @staticmethod
    def _deserialize_report(model: ReportModel) -> Report:
        """Собрать доменный отчёт из ORM-модели."""

        payload_dict: dict[str, Any] = model.payload
        meta_dict = payload_dict.get('meta') or {}
        payload = ReportPayload(
            meta=ReportPayloadMeta(
                check_id=UUID(meta_dict.get('check_id', model.check_id)),
                generated_at=_parse_datetime(
                    meta_dict.get('generated_at', model.created_at.isoformat()),
                ),
                schema_version=int(meta_dict.get('schema_version', 1)),
                modules=list(meta_dict.get('modules') or []),
                disclaimers=list(meta_dict.get('disclaimers') or []),
            ),
            sections=dict(payload_dict.get('sections') or {}),
        )
        return Report(
            id=model.id,
            check_id=model.check_id,
            created_at=model.created_at,
            status=model.status,
            modules=list(model.modules),
            payload=payload,
        )


def _parse_datetime(value: str) -> datetime:
    """Распарсить ISO-дatetime без потери таймзоны."""

    return datetime.fromisoformat(value)
