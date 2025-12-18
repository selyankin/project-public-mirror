"""Инфраструктурные утилиты для подключения к БД."""

from __future__ import annotations

from collections.abc import AsyncIterator
from contextlib import asynccontextmanager

from sqlalchemy.ext.asyncio import (
    AsyncEngine,
    AsyncSession,
    async_sessionmaker,
    create_async_engine,
)
from sqlalchemy.pool import NullPool

from shared.kernel.settings import Settings, get_settings

_engine: AsyncEngine | None = None
_session_factory: async_sessionmaker[AsyncSession] | None = None


def _resolve_dsn(settings: Settings) -> str:
    """Определить DSN, учитывая обратную совместимость."""

    return getattr(settings, 'DB_DSN', None) or settings.DATABASE_URL


def create_engine(settings: Settings) -> AsyncEngine:
    """Создать AsyncEngine с настройками приложения."""

    dsn = _resolve_dsn(settings)
    kwargs: dict[str, object] = {
        'echo': getattr(settings, 'DB_ECHO', False),
        'future': True,
    }
    pool_size = getattr(settings, 'DB_POOL_SIZE', None)
    max_overflow = getattr(settings, 'DB_MAX_OVERFLOW', None)

    if dsn.startswith('sqlite'):
        kwargs['poolclass'] = NullPool
    else:
        if pool_size is not None:
            kwargs['pool_size'] = pool_size
        if max_overflow is not None:
            kwargs['max_overflow'] = max_overflow

    return create_async_engine(dsn, **kwargs)


def get_engine() -> AsyncEngine:
    """Лениво вернуть экземпляр AsyncEngine."""

    global _engine
    if _engine is None:
        settings = get_settings()
        _engine = create_engine(settings)
    return _engine


def create_sessionmaker(
    engine: AsyncEngine,
) -> async_sessionmaker[AsyncSession]:
    """Создать фабрику сессий SQLAlchemy."""

    return async_sessionmaker(
        engine,
        expire_on_commit=False,
        autoflush=False,
        autocommit=False,
    )


def get_session_factory() -> async_sessionmaker[AsyncSession]:
    """Лениво вернуть фабрику сессий."""

    global _session_factory
    if _session_factory is None:
        _session_factory = create_sessionmaker(get_engine())
    return _session_factory


@asynccontextmanager
async def session_scope(
    session_factory: async_sessionmaker[AsyncSession],
) -> AsyncIterator[AsyncSession]:
    """Асинхронный контекстный менеджер сессии."""

    session = session_factory()
    try:
        yield session
        await session.commit()
    except Exception:
        await session.rollback()
        raise
    finally:
        await session.close()


async def get_db_session() -> AsyncIterator[AsyncSession]:
    """Асинхронный генератор сессий по умолчанию."""

    async with session_scope(get_session_factory()) as session:
        yield session
