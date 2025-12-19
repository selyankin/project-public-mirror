"""Сквозной тест: check -> report."""

from __future__ import annotations

import asyncio
import importlib
import os
import sys
from pathlib import Path
from types import ModuleType
from typing import Any

import httpx
import pytest
from asgi_lifespan import LifespanManager
from sqlalchemy import text

from shared.kernel.bootstrap import create_app
from shared.kernel.db import create_engine
from shared.kernel.settings import get_settings

PROJECT_ROOT = Path(__file__).resolve().parents[3]

pytestmark = pytest.mark.integration


@pytest.fixture(scope='session', autouse=True)
def integration_env():
    """Гарантировать, что тесты знают о режиме DB+FIAS stub."""

    dsn = os.getenv('DB_DSN')
    if not dsn:
        pytest.skip('DB_DSN is not configured for integration tests')

    overrides = {
        'STORAGE_MODE': 'db',
        'FIAS_MODE': 'stub',
    }
    previous: dict[str, str | None] = {}
    for key, value in overrides.items():
        previous[key] = os.environ.get(key)
        os.environ[key] = value

    get_settings.cache_clear()
    try:
        yield dsn
    finally:
        for key, value in previous.items():
            if value is None:
                os.environ.pop(key, None)
            else:
                os.environ[key] = value
        get_settings.cache_clear()


@pytest.fixture(scope='session', autouse=True)
def migrated_db(integration_env: str) -> None:
    """Применить миграции перед запуском интеграционных тестов."""

    try:
        command, ConfigCls = _load_alembic()
    except ModuleNotFoundError:
        pytest.skip('alembic package is not available')

    if _schema_exists():
        return

    config = ConfigCls(str(PROJECT_ROOT / 'alembic.ini'))
    command.upgrade(config, 'head')


@pytest.fixture(autouse=True)
async def clean_database() -> None:
    """Очистить основные таблицы перед и после теста."""

    await _truncate_tables()
    try:
        yield
    finally:
        await _truncate_tables()


async def _truncate_tables() -> None:
    """Удалить данные из таблиц проверки и отчётов."""

    engine = create_engine(get_settings())
    async with engine.begin() as connection:
        await connection.execute(
            text(
                'TRUNCATE TABLE check_cache, check_results, reports '
                'RESTART IDENTITY CASCADE',
            ),
        )
    await engine.dispose()


def _schema_exists() -> bool:
    """Проверить, развёрнуты ли основные таблицы."""

    async def _check() -> bool:
        engine = create_engine(get_settings())
        try:
            async with engine.begin() as connection:
                result = await connection.execute(
                    text(
                        "select 1 from information_schema.tables "
                        "where table_schema = 'public' "
                        "and table_name = 'check_results'",
                    ),
                )
                return result.scalar() is not None
        finally:
            await engine.dispose()

    return asyncio.run(_check())


def _load_alembic() -> tuple[ModuleType, type]:
    """Импортировать Alembic, не задевая локальную папку миграций."""

    removed: list[tuple[int, str]] = []
    try:
        for index in reversed(range(len(sys.path))):
            path = Path(sys.path[index]).resolve()
            if path == PROJECT_ROOT:
                removed.append((index, sys.path.pop(index)))
        command_module = importlib.import_module('alembic.command')
        config_module = importlib.import_module('alembic.config')
        ConfigCls: Any = config_module.Config
        return command_module, ConfigCls
    finally:
        for index, value in sorted(removed, key=lambda item: item[0]):
            sys.path.insert(index, value)


@pytest.mark.asyncio
async def test_user_flow_check_and_report() -> None:
    """Весь поток проверки адреса и формирования отчёта."""

    app = create_app()
    async with LifespanManager(app):
        transport = httpx.ASGITransport(app=app)
        async with httpx.AsyncClient(
            transport=transport,
            base_url='http://test',
        ) as client:
            check_response = await client.post(
                '/v1/check',
                json={
                    'type': 'address',
                    'query': 'г. Москва, ул. Тверская, 1',
                },
            )
            assert check_response.status_code == 200
            check_payload = check_response.json()
            check_id = check_payload.get('check_id')
            assert check_id, 'check_id is missing in check response'
            fias_block = check_payload.get('fias')
            assert fias_block is not None
            assert 'normalized' in fias_block

            report_response = await client.post(
                '/v1/reports',
                json={
                    'check_id': check_id,
                    'modules': ['base_summary'],
                },
            )
            assert report_response.status_code == 200
            report_payload = report_response.json()
            report_id = report_payload.get('report_id')
            assert report_id, 'report_id is missing in report response'

            fetch_response = await client.get(f'/v1/reports/{report_id}')
            assert fetch_response.status_code == 200
            full_report = fetch_response.json()
            assert full_report['check_id'] == check_id
            payload_meta = full_report['payload']['meta']
            assert payload_meta['check_id'] == check_id
            assert 'base_summary' in full_report['payload']['sections']
