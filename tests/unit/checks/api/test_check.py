import pytest
from fastapi.testclient import TestClient

from shared.kernel.bootstrap import create_app
from shared.kernel.settings import get_settings


@pytest.fixture(autouse=True)
def configure_env(monkeypatch):
    monkeypatch.setenv('DATABASE_URL', 'postgresql://localhost/flaffy')
    monkeypatch.setenv(
        'DB_DSN',
        'postgresql+asyncpg://postgres:postgres@localhost:5432/flaffy',
    )
    monkeypatch.setenv('SERVICE_NAME', 'flaffy-api')
    monkeypatch.setenv('APP_ENV', 'test')
    monkeypatch.setenv('LOG_LEVEL', 'INFO')
    monkeypatch.setenv('DEBUG', 'false')
    monkeypatch.setenv('STORAGE_MODE', 'memory')
    get_settings.cache_clear()
    yield
    get_settings.cache_clear()


def make_client() -> TestClient:
    app = create_app()
    return TestClient(app)


def test_check_endpoint_returns_risk_card():
    client = make_client()
    response = client.post(
        '/v1/check',
        json={'type': 'address', 'query': 'ул мира 7'},
    )
    assert response.status_code == 200
    data = response.json()
    assert {'score', 'level', 'summary', 'signals'} <= data.keys()
    assert data['address_source'] == 'stub'
    assert data['address_confidence'] is not None
    assert data['check_id'] is not None
    assert 'fias' not in data


def test_check_endpoint_handles_url():
    client = make_client()
    response = client.post(
        '/v1/check',
        json={'type': 'url', 'query': 'https://example.com'},
    )
    assert response.status_code == 200
    assert any(
        signal['code'] == 'url_not_supported_yet'
        for signal in response.json()['signals']
    )


def test_check_endpoint_validates_query():
    client = make_client()
    response = client.post(
        '/v1/check',
        json={'type': 'address', 'query': '   '},
    )
    assert response.status_code == 422


def test_legacy_endpoint_still_works():
    client = make_client()
    response = client.post('/v1/check/address', json={'address': 'ул мира 7'})
    assert response.status_code == 200


def test_check_endpoint_includes_fias_when_available():
    client = make_client()
    response = client.post(
        '/v1/check',
        json={'type': 'address', 'query': 'г. Москва, ул. Тверская, 1'},
    )
    assert response.status_code == 200
    data = response.json()
    assert data['fias']['fias_id'] == 'moscow-001'
