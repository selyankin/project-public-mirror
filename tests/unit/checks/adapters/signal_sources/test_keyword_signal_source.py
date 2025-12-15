from src.checks.adapters.signal_sources.keyword_signal_source import (
    KeywordSignalSource,
)
from src.checks.domain.value_objects.address import (
    normalize_address,
    normalize_address_raw,
)


def _normalized(text: str):
    return normalize_address(normalize_address_raw(text))


def test_keyword_source_rules_and_order():
    source = KeywordSignalSource({})
    signals = source.collect(_normalized("общежитие жк апарт 123"))
    assert [signal.code for signal in signals] == [
        "possible_apartments",
        "hostel_keyword",
        "residential_complex_hint",
    ]


def test_keyword_source_incomplete_rule():
    source = KeywordSignalSource({})
    signals = source.collect(_normalized("москва"))
    assert [signal.code for signal in signals] == ["address_incomplete"]


def test_keyword_source_severity_from_catalog():
    source = KeywordSignalSource({})
    signals = source.collect(_normalized("общежитие 5"))
    hostel_signal = next(
        signal for signal in signals if signal.code == "hostel_keyword"
    )
    assert hostel_signal.severity.value == 4
