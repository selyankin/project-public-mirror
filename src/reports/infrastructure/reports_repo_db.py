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
    ReportPayloadAddress,
    ReportPayloadMeta,
    ReportPayloadRisk,
    ReportPayloadSignal,
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

        return {
            'title': payload.title,
            'summary': payload.summary,
            'address': {
                'raw': payload.address.raw,
                'normalized': payload.address.normalized,
                'confidence': payload.address.confidence,
                'source': payload.address.source,
            },
            'risk': {
                'score': payload.risk.score,
                'level': payload.risk.level,
                'summary': payload.risk.summary,
            },
            'signals': [
                {
                    'code': signal.code,
                    'title': signal.title,
                    'description': signal.description,
                    'severity': signal.severity,
                }
                for signal in payload.signals
            ],
            'disclaimers': list(payload.disclaimers),
            'generated_from': {
                'check_id': str(payload.generated_from.check_id),
                'generated_at': payload.generated_from.generated_at.isoformat(),
            },
        }

    @staticmethod
    def _deserialize_report(model: ReportModel) -> Report:
        """Собрать доменный отчёт из ORM-модели."""

        payload_dict: dict[str, Any] = model.payload
        address_dict = payload_dict['address']
        risk_dict = payload_dict['risk']
        signals = [
            ReportPayloadSignal(
                code=item['code'],
                title=item['title'],
                description=item['description'],
                severity=item['severity'],
            )
            for item in payload_dict.get('signals', [])
        ]
        meta = payload_dict['generated_from']
        payload = ReportPayload(
            title=payload_dict['title'],
            summary=payload_dict['summary'],
            address=ReportPayloadAddress(
                raw=address_dict.get('raw'),
                normalized=address_dict['normalized'],
                confidence=address_dict.get('confidence'),
                source=address_dict.get('source'),
            ),
            risk=ReportPayloadRisk(
                score=risk_dict['score'],
                level=risk_dict['level'],
                summary=risk_dict['summary'],
            ),
            signals=signals,
            disclaimers=list(payload_dict.get('disclaimers', [])),
            generated_from=ReportPayloadMeta(
                check_id=UUID(meta['check_id']),
                generated_at=_parse_datetime(meta['generated_at']),
            ),
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
