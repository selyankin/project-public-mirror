"""Сквозные тесты сценария check -> report."""

from __future__ import annotations

import httpx
import pytest

pytestmark = pytest.mark.integration


@pytest.mark.asyncio
async def test_user_flow_check_to_report_base_module(app_fixture) -> None:
    """Проверяем успешный поток для базового модуля отчёта."""

    async with _client(app_fixture) as client:
        check_id, check_payload = await _perform_check(client)
        assert check_payload.get('fias') is not None

        report_response = await _create_report(
            client,
            check_id,
            ['base_summary', 'address_quality', 'risk_signals'],
        )
        assert report_response.status_code == 200
        report_id = report_response.json()['report_id']

        report_payload = await _fetch_report(client, report_id)
        assert report_payload['check_id'] == check_id

        meta = report_payload['payload']['meta']
        assert meta['check_id'] == check_id
        assert 'base_summary' in meta['modules']

        sections = report_payload['payload']['sections']
        base_section = sections.get('base_summary') or {}
        assert 'risk_level' in base_section
        assert 'address' in base_section
        assert sections.get('address_quality')
        assert sections.get('risk_signals')


@pytest.mark.asyncio
async def test_user_flow_report_paid_module_denied(app_fixture) -> None:
    """Платный модуль без разрешения даёт 402."""

    async with _client(app_fixture) as client:
        check_id, _ = await _perform_check(client)

        response = await _create_report(
            client,
            check_id,
            ['fias_normalization'],
        )
        assert response.status_code == 402
        detail = response.json()['detail']
        assert 'fias_normalization' in detail.get('modules', [])
        assert 'payment' in detail.get('message', '')


@pytest.mark.asyncio
async def test_user_flow_unknown_module_400(app_fixture) -> None:
    """Неизвестный модуль возвращает понятную ошибку."""

    async with _client(app_fixture) as client:
        check_id, _ = await _perform_check(client)

        response = await _create_report(client, check_id, ['no_such_module'])
        assert response.status_code == 400
        detail = response.json()['detail']
        assert detail.get('modules') == ['no_such_module']
        assert 'unknown module' in detail.get('message', '')


async def _perform_check(
    client: httpx.AsyncClient,
) -> tuple[str, dict[str, object]]:
    """Создать проверку адреса и вернуть идентификатор."""

    response = await client.post(
        '/v1/check',
        json={
            'type': 'address',
            'query': 'г. Москва, ул. Тверская, 1',
        },
    )
    assert response.status_code == 200
    payload = response.json()
    check_id = payload.get('check_id')
    assert check_id, 'check_id is missing'
    return check_id, payload


async def _create_report(
    client: httpx.AsyncClient,
    check_id: str,
    modules: list[str],
) -> httpx.Response:
    """Запросить генерацию отчёта по check_id."""

    return await client.post(
        '/v1/reports',
        json={
            'check_id': check_id,
            'modules': modules,
        },
    )


async def _fetch_report(
    client: httpx.AsyncClient,
    report_id: str,
) -> dict[str, object]:
    """Получить сохранённый отчёт."""

    response = await client.get(f'/v1/reports/{report_id}')
    assert response.status_code == 200
    return response.json()


def _client(app):
    """Создать httpx клиент с ASGI transport."""

    transport = httpx.ASGITransport(app=app, lifespan='off')
    return httpx.AsyncClient(
        transport=transport,
        base_url='http://test',
    )
