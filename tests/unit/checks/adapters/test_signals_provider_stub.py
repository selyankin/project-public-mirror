from checks.adapters.signals_provider_stub import SignalsProviderStub
from checks.domain.value_objects.address import (
    normalize_address,
    normalize_address_raw,
)


def _normalized(text: str):
    return normalize_address(normalize_address_raw(text))


def _signals(text: str):
    provider = SignalsProviderStub({})
    return provider.collect(_normalized(text))


def test_incomplete_address_signal_triggered():
    signals = _signals('москва')
    assert len(signals) == 1
    assert signals[0].code == 'address_incomplete'


def test_apartments_signal():
    signals = _signals('ул ленина 10 апарт')
    codes = [signal.code for signal in signals]
    assert 'possible_apartments' in codes
    assert 'address_incomplete' not in codes


def test_hostel_signal():
    signals = _signals('общежитие ул мира 7')
    assert any(signal.code == 'hostel_keyword' for signal in signals)


def test_residential_complex_signal():
    signals = _signals('жк северный ул мира 7')
    assert any(signal.code == 'residential_complex_hint' for signal in signals)


def test_signal_order_stability():
    signals = _signals('общежитие жк апарт 123')
    assert [signal.code for signal in signals] == [
        'possible_apartments',
        'hostel_keyword',
        'residential_complex_hint',
    ]


def test_returns_tuple_of_risk_signals():
    signals = _signals('москва')
    assert isinstance(signals, tuple)
    assert all(hasattr(signal, 'code') for signal in signals)
