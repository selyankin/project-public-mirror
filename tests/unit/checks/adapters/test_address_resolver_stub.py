from src.checks.adapters.address_resolver_stub import AddressResolverStub
from src.checks.domain.value_objects.address import (
    AddressNormalized,
    normalize_address_raw,
)


def resolver():
    return AddressResolverStub({})


def test_normalize_returns_address_normalized():
    raw = normalize_address_raw('  Main STREET 12 ')
    normalized = resolver().normalize(raw)
    assert isinstance(normalized, AddressNormalized)
    assert normalized.normalized == 'main street 12'


def test_normalization_is_deterministic():
    raw = normalize_address_raw('Foo,  Bar')
    resolver_instance = resolver()
    first = resolver_instance.normalize(raw)
    second = resolver_instance.normalize(raw)
    assert first.normalized == 'foo, bar'
    assert first == second
