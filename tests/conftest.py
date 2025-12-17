import os

import pytest

from src.shared.kernel.settings import get_settings


@pytest.fixture(autouse=True)
def _configure_settings_env():
    """Гарантировать корректные настройки окружения в тестах."""

    os.environ['DATABASE_URL'] = (
        'postgresql+psycopg://user:pass@localhost:5432/test'
    )
    os.environ.setdefault('APP_ENV', 'local')
    os.environ.setdefault('LOG_LEVEL', 'INFO')
    get_settings.cache_clear()
    yield
    get_settings.cache_clear()
