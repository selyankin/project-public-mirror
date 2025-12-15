import pytest
from fastapi.testclient import TestClient

from src.shared.kernel.bootstrap import create_app
from src.shared.kernel.settings import get_settings


@pytest.fixture(autouse=True)
def configure_env(monkeypatch):
    monkeypatch.setenv('DATABASE_URL', 'postgresql://localhost/mirano')
    monkeypatch.setenv('SERVICE_NAME', 'mirano-api')
    monkeypatch.setenv('APP_ENV', 'test')
    monkeypatch.setenv('LOG_LEVEL', 'INFO')
    monkeypatch.setenv('DEBUG', 'false')
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
