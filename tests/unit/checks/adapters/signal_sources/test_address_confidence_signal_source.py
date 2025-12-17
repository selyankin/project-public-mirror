"""Тесты источника сигналов confidence/source."""

from checks.adapters.signal_sources.address_confidence_signal_source import (
    AddressConfidenceSignalSource,
)
from checks.application.ports.signal_sources import SignalsContext
from checks.domain.value_objects.address import (
    AddressNormalized,
    normalize_address,
    normalize_address_raw,
)


def _normalized(text: str) -> AddressNormalized:
    normalized = normalize_address(normalize_address_raw(text))
    normalized.confidence = 'high'
    normalized.source = 'fias'
    return normalized


def test_unknown_confidence_and_stub_source() -> None:
    """unknown + stub -> два сигнала."""

    normalized = _normalized('г. Москва')
    normalized.confidence = 'unknown'
    normalized.source = 'stub'
    source = AddressConfidenceSignalSource({})

    context = SignalsContext(address=normalized)
    signals = source.collect(normalized, context=context)

    codes = [signal.code for signal in signals]
    assert codes == [
        'address_confidence_unknown',
        'address_source_stub',
    ]


def test_low_confidence_no_stub_signal() -> None:
    """low + fias -> только сигнал уверенности."""

    normalized = _normalized('г. Москва')
    normalized.confidence = 'low'
    normalized.source = 'fias'
    source = AddressConfidenceSignalSource({})

    context = SignalsContext(address=normalized)
    signals = source.collect(normalized, context=context)

    codes = [signal.code for signal in signals]
    assert codes == ['address_confidence_low']


def test_high_confidence_stub_only() -> None:
    """high + stub -> только сигнал источника."""

    normalized = _normalized('г. Москва')
    normalized.confidence = 'high'
    normalized.source = 'stub'
    source = AddressConfidenceSignalSource({})

    context = SignalsContext(address=normalized)
    signals = source.collect(normalized, context=context)

    codes = [signal.code for signal in signals]
    assert codes == ['address_source_stub']
