import asyncio
import os
from types import SimpleNamespace

import pytest

from shared.kernel import db


class DummySession:
    def __init__(self) -> None:
        self.commits = 0
        self.rollbacks = 0
        self.closed = 0

    async def commit(self) -> None:
        self.commits += 1

    async def rollback(self) -> None:
        self.rollbacks += 1

    async def close(self) -> None:
        self.closed += 1


class DummyFactory:
    def __init__(self) -> None:
        self.instance: DummySession | None = None

    def __call__(self) -> DummySession:
        self.instance = DummySession()
        return self.instance


@pytest.mark.asyncio
async def test_session_scope_commits_and_closes():
    """Контекст сессии коммитит транзакцию и закрывает сессию."""

    factory = DummyFactory()

    async with db.session_scope(factory) as session:
        assert session.commits == 0

    assert factory.instance is not None
    assert factory.instance.commits == 1
    assert factory.instance.closed == 1


@pytest.mark.asyncio
async def test_session_scope_rolls_back_on_error():
    """При ошибке транзакция откатывается."""

    factory = DummyFactory()

    with pytest.raises(RuntimeError):
        async with db.session_scope(factory):
            raise RuntimeError('boom')

    assert factory.instance is not None
    assert factory.instance.rollbacks == 1
    assert factory.instance.closed == 1


def test_create_sessionmaker_configures_defaults():
    """Фабрика сессий выключает expire/autoflush/autocommit."""

    settings = SimpleNamespace(
        DB_DSN=os.getenv('DB_DSN'),
        DATABASE_URL=os.getenv('DATABASE_URL'),
        DB_ECHO=False,
        DB_POOL_SIZE=None,
        DB_MAX_OVERFLOW=None,
    )
    engine = db.create_engine(
        SimpleNamespace(
            DB_DSN=settings.DB_DSN,
            DATABASE_URL=settings.DATABASE_URL,
            DB_ECHO=settings.DB_ECHO,
            DB_POOL_SIZE=settings.DB_POOL_SIZE,
            DB_MAX_OVERFLOW=settings.DB_MAX_OVERFLOW,
        ),
    )
    try:
        factory = db.create_sessionmaker(engine)
        assert factory.kw.get('expire_on_commit') is False
        assert factory.kw.get('autoflush') is False
        assert factory.kw.get('autocommit') is False
    finally:
        asyncio.run(engine.dispose())


@pytest.mark.asyncio
async def test_get_db_session_reads_from_request_state():
    """Зависимость FastAPI использует фабрику из состояния приложения."""

    factory = DummyFactory()
    state = SimpleNamespace(db_session_factory=factory)
    request = SimpleNamespace(app=SimpleNamespace(state=state))

    session_gen = db.get_db_session(request)
    session = await anext(session_gen)
    assert session is factory.instance
    await session_gen.aclose()
    assert factory.instance.closed == 1


@pytest.mark.asyncio
async def test_get_db_session_requires_configured_factory():
    """Если фабрика не задана, поднимается ошибка."""

    request = SimpleNamespace(app=SimpleNamespace(state=SimpleNamespace()))
    with pytest.raises(RuntimeError):
        session_gen = db.get_db_session(request)
        await anext(session_gen)
