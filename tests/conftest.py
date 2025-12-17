import os
import sys
from pathlib import Path

import pytest
from shared.kernel.settings import get_settings


@pytest.fixture(autouse=True)
def _configure_settings_env():
    """Гарантировать корректные настройки окружения в тестах."""

    src_path = Path(__file__).parent.parent / 'src'
    sys.path.insert(0, str(src_path))

    os.environ['DATABASE_URL'] = (
        'postgresql+psycopg://user:pass@localhost:5432/test'
    )
    os.environ.setdefault('APP_ENV', 'local')
    os.environ.setdefault('LOG_LEVEL', 'INFO')
    get_settings.cache_clear()
    yield
    get_settings.cache_clear()
