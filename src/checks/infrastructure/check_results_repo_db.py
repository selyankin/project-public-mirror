"""Хранилище результатов проверок на SQLAlchemy."""

from __future__ import annotations

from collections.abc import Mapping
from typing import Any
from uuid import UUID

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker

from checks.application.ports.checks import CheckResultsRepoPort
from checks.domain.entities.check_result import CheckResultSnapshot
from checks.domain.value_objects.address import AddressNormalized, AddressRaw
from risks.domain.entities.risk_card import RiskCard, RiskSignal
from shared.infra.db.models.check_result import CheckResultModel
from shared.kernel.db import session_scope


class CheckResultsRepoDb(CheckResultsRepoPort):
    """Сохраняет и читает результаты проверок через БД."""

    __slots__ = ('_session_factory',)

    def __init__(
        self,
        session_factory: async_sessionmaker[AsyncSession],
    ) -> None:
        """Принять фабрику сессий SQLAlchemy."""

        self._session_factory = session_factory

    async def save(self, result: CheckResultSnapshot) -> UUID:
        """Сохранить снимок проверки и вернуть его идентификатор."""

        payload = self._serialize_snapshot(result)
        async with session_scope(self._session_factory) as session:
            model = CheckResultModel(
                created_at=result.created_at,
                schema_version=result.schema_version,
                kind=result.kind,
                input_value=result.raw_input,
                payload=payload,
            )
            session.add(model)
            await session.flush()
            return model.id

    async def get(self, check_id: UUID) -> CheckResultSnapshot | None:
        """Получить ранее сохранённый снимок по идентификатору."""

        async with session_scope(self._session_factory) as session:
            stmt = select(CheckResultModel).where(
                CheckResultModel.id == check_id
            )
            model = await session.scalar(stmt)
            if model is None:
                return None

            return self._deserialize_snapshot(model)

    @staticmethod
    def _serialize_snapshot(
        snapshot: CheckResultSnapshot,
    ) -> dict[str, Any]:
        """Подготовить JSON для сохранения в колонку payload."""

        normalized = snapshot.normalized_address
        payload: dict[str, Any] = {
            'normalized_address': {
                'raw': normalized.raw.value,
                'normalized': normalized.normalized,
                'tokens': list(normalized.tokens),
                'confidence': normalized.confidence,
                'source': normalized.source,
            },
            'signals': [signal.to_dict() for signal in snapshot.signals],
            'risk_card': snapshot.risk_card.to_dict(),
        }
        if snapshot.fias_payload:
            payload['fias'] = snapshot.fias_payload
        if snapshot.fias_debug_raw:
            payload['fias_debug_raw'] = snapshot.fias_debug_raw
        if snapshot.listing_payload:
            payload['listing'] = snapshot.listing_payload
        if snapshot.listing_error:
            payload['listing_error'] = snapshot.listing_error
        if snapshot.sources_payload:
            payload['sources'] = snapshot.sources_payload
        return payload

    @staticmethod
    def _deserialize_snapshot(model: CheckResultModel) -> CheckResultSnapshot:
        """Восстановить доменный снимок из ORM-модели."""

        payload: Mapping[str, Any] = model.payload
        normalized_payload = payload['normalized_address']
        address = AddressNormalized(
            raw=AddressRaw(normalized_payload['raw']),
            normalized=normalized_payload['normalized'],
            tokens=tuple(normalized_payload['tokens']),
            confidence=normalized_payload.get('confidence', 'unknown'),
            source=normalized_payload.get('source', 'stub'),
        )
        signals_data = payload.get('signals', [])
        signals = [RiskSignal(item) for item in signals_data]
        risk_card = RiskCard(payload['risk_card'])

        return CheckResultSnapshot(
            raw_input=model.input_value,
            normalized_address=address,
            signals=signals,
            risk_card=risk_card,
            created_at=model.created_at,
            kind=model.kind,
            schema_version=model.schema_version,
            fias_payload=payload.get('fias'),
            fias_debug_raw=payload.get('fias_debug_raw'),
            listing_payload=payload.get('listing'),
            listing_error=payload.get('listing_error'),
            sources_payload=payload.get('sources'),
        )
