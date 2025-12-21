"""Инфраструктурные фикстуры интеграционных тестов."""

from __future__ import annotations

import importlib
import os
import sys
from pathlib import Path
from typing import Any

import pytest
from asgi_lifespan import LifespanManager
from pytest import MonkeyPatch
from sqlalchemy import text

from shared.kernel.bootstrap import create_app
from shared.kernel.db import create_engine
from shared.kernel.settings import Settings, get_settings

PROJECT_ROOT = Path(__file__).resolve().parents[2]


@pytest.fixture(scope='session')
def test_settings() -> Settings:
    """Сконфигурировать окружение для интеграционных тестов."""

    dsn = os.getenv('DB_DSN')
    if not dsn:
        pytest.skip('DB_DSN env is required for integration tests.')

    patch = MonkeyPatch()
    patch.setenv('STORAGE_MODE', 'db')
    patch.setenv('FIAS_MODE', 'stub')
    patch.setenv('REPORTS_ALLOW_PAID_MODULES', 'false')

    get_settings.cache_clear()
    try:
        settings = get_settings()
        yield settings
    finally:
        get_settings.cache_clear()
        patch.undo()


@pytest.fixture(scope='session')
def apply_migrations_once(test_settings: Settings) -> None:
    """Применить актуальные миграции один раз за сессию."""

    command_module, config_cls = _load_alembic_modules()
    config = config_cls(str(PROJECT_ROOT / 'alembic.ini'))
    command_module.upgrade(config, 'head')


@pytest.fixture(autouse=True)
async def db_cleaner(apply_migrations_once: None) -> None:
    """Чистить ключевые таблицы перед и после каждого теста."""

    await _truncate_tables()
    try:
        yield
    finally:
        await _truncate_tables()


@pytest.fixture
async def app_fixture(test_settings: Settings):
    """Поднять FastAPI приложение с реальным lifecycle."""

    app = create_app()
    async with LifespanManager(app):
        yield app


async def _truncate_tables() -> None:
    """Удалить данные из таблиц кэша, проверок и отчётов."""

    engine = create_engine(get_settings())
    try:
        async with engine.begin() as connection:
            await connection.execute(
                text(
                    'TRUNCATE TABLE check_cache, reports, check_results '
                    'RESTART IDENTITY CASCADE',
                ),
            )
    finally:
        await engine.dispose()


def _load_alembic_modules() -> tuple[Any, type]:
    """Импортировать Alembic, временно скрыв локальный пакет миграций."""

    removed: list[tuple[int, str]] = []
    for index in reversed(range(len(sys.path))):
        path = Path(sys.path[index]).resolve()
        if path == PROJECT_ROOT:
            removed.append((index, sys.path.pop(index)))
    try:
        command_module = importlib.import_module('alembic.command')
        config_module = importlib.import_module('alembic.config')
        ConfigCls: Any = config_module.Config
        return command_module, ConfigCls
    finally:
        for index, value in sorted(removed, key=lambda item: item[0]):
            sys.path.insert(index, value)
