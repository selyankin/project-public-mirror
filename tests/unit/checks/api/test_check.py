import pytest
from fastapi.testclient import TestClient

from src.shared.kernel.bootstrap import create_app
from src.shared.kernel.settings import get_settings


@pytest.fixture(autouse=True)
def configure_env(monkeypatch):
    monkeypatch.setenv("DATABASE_URL", "postgresql://localhost/mirano")
    monkeypatch.setenv("SERVICE_NAME", "mirano-api")
    monkeypatch.setenv("APP_ENV", "test")
    monkeypatch.setenv("LOG_LEVEL", "INFO")
    monkeypatch.setenv("DEBUG", "false")
    get_settings.cache_clear()
    yield
    get_settings.cache_clear()


def make_client() -> TestClient:
    app = create_app()
    return TestClient(app)


def test_check_endpoint_returns_risk_card():
    client = make_client()
    response = client.post("/v1/check", json={"address": "ул мира 7"})
    assert response.status_code == 200
    data = response.json()
    assert {"score", "level", "summary", "signals"} <= data.keys()


def test_check_endpoint_validates_address():
    client = make_client()
    response = client.post("/v1/check", json={"address": "   "})
    assert response.status_code == 422


def test_check_endpoint_detects_apartments():
    client = make_client()
    response = client.post("/v1/check", json={"address": "ул мира 7 апарт"})
    assert response.status_code == 200
    data = response.json()
    assert any(
        signal["code"] == "possible_apartments" for signal in data["signals"]
    )
