import pytest

from checks.adapters.address_resolver_stub import AddressResolverStub
from checks.domain.value_objects.address import (
    AddressNormalized,
    normalize_address_raw,
)

pytestmark = pytest.mark.asyncio


def resolver():
    return AddressResolverStub({})


async def test_normalize_returns_address_normalized():
    raw = normalize_address_raw('  Main STREET 12 ')
    normalized = await resolver().normalize(raw)
    assert isinstance(normalized, AddressNormalized)
    assert normalized.normalized == 'main street 12'
    assert normalized.source == 'stub'


async def test_normalization_is_deterministic():
    raw = normalize_address_raw('Foo,  Bar')
    resolver_instance = resolver()
    first = await resolver_instance.normalize(raw)
    second = await resolver_instance.normalize(raw)
    assert first.normalized == 'foo, bar'
    assert first == second
