"""Тесты интеграции резолвера адресов с ФИАС."""

import pytest

from checks.domain.value_objects.address import normalize_address_raw
from checks.infrastructure.address_resolver_fias import FiasAddressResolver
from checks.infrastructure.fias.errors import FiasError


class _BaseDummyClient:
    def __init__(self, *args, **kwargs):
        """Поддерживает интерфейс реального клиента."""


def test_fias_resolver_marks_source_on_success(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """Успешный вызов клиента должен выставить source=fias."""

    class DummyClient(_BaseDummyClient):
        def search_address_item(self, value: str):
            return {'value': value}

    monkeypatch.setattr(
        'checks.infrastructure.address_resolver_fias.FiasClient',
        DummyClient,
    )

    resolver = FiasAddressResolver('https://test', 'token', 1.0)
    raw = normalize_address_raw('г. Москва, ул. Тверская, д. 1')
    normalized = resolver.normalize(raw)

    assert normalized.source == 'fias'


def test_fias_resolver_fallback_keeps_stub_source(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """Ошибка клиента оставляет source=stub."""

    class FailingClient(_BaseDummyClient):
        def search_address_item(self, value: str):
            raise FiasError(f'fail on {value}')

    monkeypatch.setattr(
        'checks.infrastructure.address_resolver_fias.FiasClient',
        FailingClient,
    )

    resolver = FiasAddressResolver('https://test', 'token', 1.0)
    raw = normalize_address_raw('г. Москва')
    normalized = resolver.normalize(raw)

    assert normalized.source == 'stub'
