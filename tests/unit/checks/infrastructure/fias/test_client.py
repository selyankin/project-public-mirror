"""Тесты транспортного клиента ФИАС."""

from collections.abc import Callable
from typing import Any
from uuid import uuid4

import httpx
import pytest

from checks.infrastructure.fias.client import FiasClient
from checks.infrastructure.fias.errors import (
    FiasServerError,
    FiasTimeoutError,
    FiasUnexpectedStatus,
)


def _build_client(
    handler: Callable[[httpx.Request], httpx.Response | None],
) -> FiasClient:
    """Создать клиента с подменой транспорта."""

    transport = httpx.MockTransport(handler)
    injected = httpx.Client(transport=transport)
    return FiasClient(
        base_url='https://fias.test',
        token='token',
        timeout_seconds=1,
        client=injected,
    )


def _success_payload() -> dict[str, Any]:
    """Вернуть минимальный корректный ответ."""

    object_guid = uuid4()
    successor_guid = uuid4()
    hierarchy_guid = uuid4()
    return {
        'object_id': 1,
        'object_level_id': 1,
        'operation_type_id': 1,
        'object_guid': str(object_guid),
        'address_type': 1,
        'full_name': 'г Москва',
        'region_code': 77,
        'is_active': True,
        'path': '/77/7800000000000',
        'address_details': {
            'postal_code': '101000',
            'ifns_ul': '7700',
            'ifns_fl': '7701',
            'ifns_tul': '7702',
            'ifns_tfl': '7703',
            'okato': '45000000000',
            'oktmo': '45000000',
            'kladr_code': '7700000000000',
            'cadastral_number': '77:00:0000000:0',
            'apart_building': '1',
            'remove_cadastr': '0',
            'oktmo_budget': '45000000',
            'is_adm_capital': '1',
            'is_mun_capital': '1',
        },
        'successor_ref': {
            'object_id': 2,
            'object_guid': str(successor_guid),
        },
        'hierarchy': [
            {
                'object_id': 3,
                'object_level_id': 3,
                'object_guid': str(hierarchy_guid),
                'full_name': 'г Москва',
                'full_name_short': 'Москва',
                'kladr_code': '7700000000000',
                'object_type': 'city',
                'hierarchy_place': 1,
                'hist_names': [
                    {
                        'name': 'Москва',
                        'short_type': 'г',
                    },
                ],
            },
        ],
        'federal_district': {
            'id': 1,
            'full_name': 'Центральный',
            'short_name': 'ЦФО',
            'center_id': 77,
        },
        'hierarchy_place': 10,
    }


def test_client_returns_dto_on_success() -> None:
    """Клиент возвращает DTO при статусе 200."""

    def handler(_: httpx.Request) -> httpx.Response:
        return httpx.Response(200, json=_success_payload())

    client = _build_client(handler)

    result = client.search_address_item('адрес')

    assert result.object_id == 1
    assert result.address_details is not None
    assert result.hierarchy is not None
    assert result.hierarchy[0].hist_names is not None


def test_client_raises_server_error() -> None:
    """Клиент выбрасывает FiasServerError при 500."""

    def handler(_: httpx.Request) -> httpx.Response:
        return httpx.Response(500, json={'description': 'boom'})

    client = _build_client(handler)

    with pytest.raises(FiasServerError) as exc:
        client.search_address_item('адрес')

    assert exc.value.description == 'boom'


def test_client_raises_unexpected_status() -> None:
    """Клиент выбрасывает FiasUnexpectedStatus при иных кодах."""

    def handler(_: httpx.Request) -> httpx.Response:
        return httpx.Response(418, text='teapot')

    client = _build_client(handler)

    with pytest.raises(FiasUnexpectedStatus) as exc:
        client.search_address_item('адрес')

    assert exc.value.status_code == 418


def test_client_wraps_timeout_error() -> None:
    """Таймаут httpx приводит к FiasTimeoutError."""

    def handler(_: httpx.Request) -> httpx.Response:
        raise httpx.ReadTimeout('boom')

    client = _build_client(handler)

    with pytest.raises(FiasTimeoutError):
        client.search_address_item('адрес')
