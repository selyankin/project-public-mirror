"""Реализация кэша результатов проверок через БД."""

from __future__ import annotations

from collections.abc import Callable
from datetime import UTC, datetime, timedelta
from uuid import UUID

from sqlalchemy import delete
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker

from checks.application.ports.checks import CheckCacheRepoPort
from checks.domain.entities.check_cache import CachedCheckEntry
from shared.infra.db.models.check_cache import CheckCacheModel
from shared.kernel.db import session_scope


class CheckCacheRepoDb(CheckCacheRepoPort):
    """Сохраняет соответствия ключей кэша и результатов проверок."""

    __slots__ = (
        '_session_factory',
        '_ttl',
        '_cache_version',
        '_now_fn',
    )

    def __init__(
        self,
        session_factory: async_sessionmaker[AsyncSession],
        *,
        ttl_seconds: int,
        cache_version: str,
        now_fn: Callable[[], datetime] | None = None,
    ) -> None:
        """Настроить репозиторий и параметры TTL."""

        self._session_factory = session_factory
        self._ttl = timedelta(seconds=ttl_seconds)
        self._cache_version = cache_version
        self._now_fn = now_fn or (lambda: datetime.now(UTC))

    async def get(self, key: str) -> CachedCheckEntry | None:
        """Вернуть запись, если ключ присутствует и не протух."""

        now = self._now_fn()
        async with session_scope(self._session_factory) as session:
            model = await session.get(CheckCacheModel, key)
            if model is None:
                return None

            if model.cache_version != self._cache_version:
                await session.delete(model)
                return None

            if model.expires_at <= now:
                await session.delete(model)
                return None

            return CachedCheckEntry(
                check_id=model.check_result_id,
                created_at=model.created_at,
                expires_at=model.expires_at,
            )

    async def set(self, key: str, check_id: UUID) -> None:
        """Сохранить или обновить запись кэша."""

        now = self._now_fn()
        expires_at = now + self._ttl
        async with session_scope(self._session_factory) as session:
            model = await session.get(CheckCacheModel, key)
            if model is None:
                model = CheckCacheModel(
                    cache_key=key,
                    check_result_id=check_id,
                    created_at=now,
                    expires_at=expires_at,
                    cache_version=self._cache_version,
                )
                session.add(model)
            else:
                model.check_result_id = check_id
                model.created_at = now
                model.expires_at = expires_at
                model.cache_version = self._cache_version

    async def cleanup(self) -> None:
        """Удалить протухшие записи (best effort)."""

        now = self._now_fn()
        async with session_scope(self._session_factory) as session:
            stmt = delete(CheckCacheModel).where(
                CheckCacheModel.expires_at <= now,
            )
            await session.execute(stmt)
