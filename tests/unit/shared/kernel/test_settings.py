import pytest

from shared.kernel.settings import Settings, get_settings


@pytest.fixture(autouse=True)
def _clear_settings_cache():
    get_settings.cache_clear()
    yield
    get_settings.cache_clear()


@pytest.fixture
def base_env(monkeypatch):
    monkeypatch.setenv('APP_ENV', 'local')
    monkeypatch.setenv('DATABASE_URL', 'postgresql://localhost/flaffy')


def test_settings_defaults():
    settings = Settings(
        APP_ENV='local',
        DATABASE_URL='postgresql://localhost/flaffy',
    )
    assert settings.LOG_LEVEL == 'INFO'
    assert settings.SERVICE_NAME == 'flaffy'
    assert settings.TIMEZONE == 'Europe/Stockholm'
    assert settings.DEBUG is False
    assert settings.FIAS_MODE == 'stub'
    assert settings.fias_enabled is False


def test_debug_mode(base_env, monkeypatch):
    monkeypatch.setenv('DEBUG', 'true')
    settings = Settings()
    assert settings.DEBUG is True

    monkeypatch.delenv('DEBUG', raising=False)

    prod_settings = Settings(
        APP_ENV='prod',
        DATABASE_URL='postgresql://localhost/flaffy',
    )
    assert prod_settings.DEBUG is False


def test_database_url_validation():
    with pytest.raises(ValueError) as exc_info:
        Settings(
            APP_ENV='local',
            DATABASE_URL='http://localhost',
        )
    assert 'DATABASE_URL must use one of' in str(exc_info.value)


def test_fias_validation_requires_fields(monkeypatch, base_env):
    monkeypatch.setenv('FIAS_MODE', 'api')
    with pytest.raises(ValueError):
        Settings()


def test_fias_api_mode_valid(monkeypatch, base_env):
    monkeypatch.setenv('FIAS_MODE', 'api')
    monkeypatch.setenv('FIAS_BASE_URL', 'https://fias.local')
    monkeypatch.setenv('FIAS_TOKEN', 'secret')
    settings = Settings()
    assert settings.fias_enabled is True


def test_get_settings_cache(base_env):
    settings1 = get_settings()
    settings2 = get_settings()
    assert settings1 is settings2

    get_settings.cache_clear()
    settings3 = get_settings()
    assert settings1 is not settings3
