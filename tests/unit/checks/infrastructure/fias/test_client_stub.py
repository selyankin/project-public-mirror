import pytest

from checks.infrastructure.fias.client_stub import StubFiasClient


@pytest.mark.asyncio
async def test_stub_returns_known_address():
    client = StubFiasClient()
    result = await client.normalize_address('ул. Тверская, Москва')
    assert result is not None
    assert 'москва' in result.normalized
    assert result.fias_id == 'moscow-001'


@pytest.mark.asyncio
async def test_stub_returns_none_for_unknown():
    client = StubFiasClient()
    result = await client.normalize_address('неизвестный адрес')
    assert result is None
