import pytest
from fastapi.testclient import TestClient
from shared.kernel.bootstrap import create_app
from shared.kernel.settings import get_settings


@pytest.fixture(autouse=True)
def configure_env(monkeypatch):
    monkeypatch.setenv('DATABASE_URL', 'postgresql://localhost/flaffy')
    monkeypatch.setenv('SERVICE_NAME', 'flaffy-api')
    monkeypatch.setenv('APP_ENV', 'test')
    monkeypatch.setenv('LOG_LEVEL', 'INFO')
    monkeypatch.setenv('DEBUG', 'false')
    get_settings.cache_clear()
    yield
    get_settings.cache_clear()


def make_client() -> TestClient:
    app = create_app()
    return TestClient(app)


def test_create_and_fetch_report_flow():
    client = make_client()
    check_response = client.post(
        '/v1/check',
        json={'type': 'address', 'query': 'ул мира 7'},
    )
    assert check_response.status_code == 200
    check_id = check_response.json()['check_id']

    create_response = client.post(
        '/v1/reports',
        json={'check_id': check_id, 'modules': ['base']},
    )
    assert create_response.status_code == 200
    report_id = create_response.json()['report_id']

    get_response = client.get(f'/v1/reports/{report_id}')
    assert get_response.status_code == 200
    data = get_response.json()
    assert data['check_id'] == check_id
    assert data['payload']['address']['normalized']
