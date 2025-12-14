import pytest
from fastapi import FastAPI
from fastapi.testclient import TestClient

from src.shared.kernel.bootstrap import create_app
from src.shared.kernel.settings import get_settings


@pytest.fixture(autouse=True)
def configure_env(monkeypatch):
    monkeypatch.setenv('DATABASE_URL', 'postgresql://localhost/mirano')
    monkeypatch.setenv('SERVICE_NAME', 'mirano-api')
    monkeypatch.setenv('LOG_LEVEL', 'INFO')
    monkeypatch.setenv('DEBUG', 'true')
    monkeypatch.setenv('APP_ENV', 'test')
    get_settings.cache_clear()
    yield
    get_settings.cache_clear()


def test_create_app_returns_fastapi():
    app = create_app()
    assert isinstance(app, FastAPI)
    assert app.title == 'mirano-api'
    assert app.debug is True


def test_health_endpoint_returns_ok():
    app = create_app()
    client = TestClient(app)
    response = client.get('/health')
    assert response.status_code == 200
    assert response.json() == {'status': 'ok'}
