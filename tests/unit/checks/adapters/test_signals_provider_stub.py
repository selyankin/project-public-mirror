import pytest

from checks.adapters.signals_provider_stub import SignalsProviderStub
from checks.domain.value_objects.address import (
    normalize_address,
    normalize_address_raw,
)

pytestmark = pytest.mark.asyncio


def _normalized(text: str):
    return normalize_address(normalize_address_raw(text))


async def _signals(text: str):
    provider = SignalsProviderStub({})
    return await provider.collect(_normalized(text))


async def test_incomplete_address_signal_triggered():
    signals = await _signals('москва')
    codes = [signal.code for signal in signals]
    assert 'address_incomplete' in codes
    assert 'address_confidence_unknown' in codes


async def test_apartments_signal():
    signals = await _signals('ул ленина 10 апарт')
    codes = [signal.code for signal in signals]
    assert 'possible_apartments' in codes
    assert 'address_incomplete' not in codes


async def test_hostel_signal():
    signals = await _signals('общежитие ул мира 7')
    assert any(signal.code == 'hostel_keyword' for signal in signals)


async def test_residential_complex_signal():
    signals = await _signals('жк северный ул мира 7')
    assert any(signal.code == 'residential_complex_hint' for signal in signals)


async def test_signal_order_stability():
    signals = await _signals('общежитие жк апарт 123')
    assert [signal.code for signal in signals] == [
        'address_confidence_unknown',
        'address_source_stub',
        'possible_apartments',
        'hostel_keyword',
        'residential_complex_hint',
    ]


async def test_returns_tuple_of_risk_signals():
    signals = await _signals('москва')
    assert isinstance(signals, tuple)
    assert all(hasattr(signal, 'code') for signal in signals)
