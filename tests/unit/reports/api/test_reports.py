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
    monkeypatch.setenv('FIAS_MODE', 'stub')
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
        json={'check_id': check_id, 'modules': ['base_summary']},
    )
    assert create_response.status_code == 200
    report_id = create_response.json()['report_id']

    get_response = client.get(f'/v1/reports/{report_id}')
    assert get_response.status_code == 200
    data = get_response.json()
    assert data['check_id'] == check_id
    assert 'base_summary' in data['payload']['sections']
    assert data['payload']['meta']['modules']


def test_create_report_unknown_module_returns_400():
    client = make_client()
    check_response = client.post(
        '/v1/check',
        json={'type': 'address', 'query': 'ул мира 7'},
    )
    check_id = check_response.json()['check_id']

    response = client.post(
        '/v1/reports',
        json={'check_id': check_id, 'modules': ['unknown']},
    )
    assert response.status_code == 400
    detail = response.json()['detail']
    assert 'unknown module' in detail['message']
    assert detail['modules'] == ['unknown']


def test_create_report_paid_module_requires_payment_returns_402():
    client = make_client()
    check_response = client.post(
        '/v1/check',
        json={'type': 'address', 'query': 'ул мира 7'},
    )
    check_id = check_response.json()['check_id']

    response = client.post(
        '/v1/reports',
        json={'check_id': check_id, 'modules': ['fias_normalization']},
    )
    assert response.status_code == 402
    detail = response.json()['detail']
    assert 'payment required' in detail['message']
    assert detail['modules'] == ['fias_normalization']


def test_create_report_empty_list_returns_400():
    client = make_client()
    check_response = client.post(
        '/v1/check',
        json={'type': 'address', 'query': 'ул мира 7'},
    )
    check_id = check_response.json()['check_id']

    response = client.post(
        '/v1/reports',
        json={'check_id': check_id, 'modules': []},
    )
    assert response.status_code == 400
    detail = response.json()['detail']
    assert 'must not be empty' in detail['message']
