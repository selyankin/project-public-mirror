"""Настройки Alembic для асинхронных миграций."""

from __future__ import annotations

import asyncio
from logging.config import fileConfig

from alembic import context
from shared.kernel.db import create_engine
from shared.kernel.db_base import Base
from shared.kernel.settings import get_settings

config = context.config

if config.config_file_name is not None:
    fileConfig(config.config_file_name)

settings = get_settings()
target_metadata = Base.metadata


def get_url() -> str:
    """Вернуть строку подключения БД."""

    return getattr(settings, 'DB_DSN', settings.DATABASE_URL)


def run_migrations_offline() -> None:
    """Запустить миграции в оффлайн-режиме."""

    url = get_url()
    context.configure(
        url=url,
        target_metadata=target_metadata,
        literal_binds=True,
        dialect_opts={'paramstyle': 'named'},
    )

    with context.begin_transaction():
        context.run_migrations()


def do_run_migrations(connection) -> None:
    """Запустить миграции, используя активное соединение."""

    context.configure(connection=connection, target_metadata=target_metadata)

    with context.begin_transaction():
        context.run_migrations()


async def run_migrations_online() -> None:
    """Запустить миграции в онлайн-режиме (async)."""

    engine = create_engine(settings)
    async with engine.begin() as connection:
        await connection.run_sync(do_run_migrations)
    await engine.dispose()


if context.is_offline_mode():
    run_migrations_offline()
else:
    asyncio.run(run_migrations_online())
