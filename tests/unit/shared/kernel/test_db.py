from types import SimpleNamespace

import pytest

from shared.kernel import db


@pytest.fixture(autouse=True)
def reset_db_module_state():
    db._engine = None
    db._session_factory = None
    yield
    db._engine = None
    db._session_factory = None


def test_get_engine_lazily_initialises_engine(monkeypatch):
    fake_engine = object()
    call_stats = {'count': 0}

    def fake_create_async_engine(url, **kwargs):
        call_stats['count'] += 1
        call_stats['url'] = url
        call_stats['kwargs'] = kwargs
        return fake_engine

    monkeypatch.setattr(db, 'create_async_engine', fake_create_async_engine)
    monkeypatch.setattr(
        db,
        'get_settings',
        lambda: SimpleNamespace(DATABASE_URL='postgresql+asyncpg://db'),
    )

    engine1 = db.get_engine()
    engine2 = db.get_engine()

    assert engine1 is engine2 is fake_engine
    assert call_stats['count'] == 1
    assert call_stats['url'] == 'postgresql+asyncpg://db'
    assert call_stats['kwargs'] == {'echo': False, 'future': True}


def test_get_session_factory_configures_async_sessionmaker(monkeypatch):
    fake_engine = object()
    factory_instance = object()
    call_stats = {}

    def fake_get_engine():
        call_stats['engine_calls'] = call_stats.get('engine_calls', 0) + 1
        return fake_engine

    def fake_sessionmaker(engine, **kwargs):
        call_stats['engine'] = engine
        call_stats['kwargs'] = kwargs
        return factory_instance

    monkeypatch.setattr(db, 'get_engine', fake_get_engine)
    monkeypatch.setattr(db, 'async_sessionmaker', fake_sessionmaker)

    factory1 = db.get_session_factory()
    factory2 = db.get_session_factory()

    assert factory1 is factory2 is factory_instance
    assert call_stats['engine_calls'] == 1
    assert call_stats['engine'] is fake_engine
    assert call_stats['kwargs'] == {
        'expire_on_commit': False,
        'autoflush': False,
        'autocommit': False,
    }


@pytest.mark.asyncio
async def test_get_db_session_yields_and_closes_session(monkeypatch):
    class DummySession:
        def __init__(self):
            self.closed = False

        async def close(self):
            self.closed = True

    dummy_session = DummySession()

    def dummy_factory():
        return dummy_session

    monkeypatch.setattr(db, 'get_session_factory', lambda: dummy_factory)

    session_gen = db.get_db_session()
    session = await anext(session_gen)

    assert session is dummy_session
    assert dummy_session.closed is False

    await session_gen.aclose()
    assert dummy_session.closed is True
