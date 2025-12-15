from src.checks.application.signals_pipeline import SignalsPipeline
from src.checks.domain.value_objects.address import (
    AddressNormalized,
    normalize_address,
    normalize_address_raw,
)
from src.risks.domain.entities.risk_card import RiskSignal


def _normalized(text: str) -> AddressNormalized:
    return normalize_address(normalize_address_raw(text))


def _signal(code: str) -> RiskSignal:
    return RiskSignal(
        {
            "code": code,
            "title": code,
            "description": code,
            "severity": "low",
        },
    )


class DummySource:
    __slots__ = ("_signals",)

    def __init__(self, signals: tuple[RiskSignal, ...]):
        self._signals = signals

    def collect(self, normalized: AddressNormalized) -> tuple[RiskSignal, ...]:
        return self._signals


def test_pipeline_deduplicates_by_code():
    source_one = DummySource((_signal("a"), _signal("b")))
    source_two = DummySource((_signal("b"), _signal("c")))
    pipeline = SignalsPipeline({"sources": [source_one, source_two]})

    result = pipeline.collect(_normalized("addr 1"))
    assert [signal.code for signal in result] == ["a", "b", "c"]


def test_pipeline_preserves_source_order():
    source_one = DummySource((_signal("a"), _signal("b")))
    source_two = DummySource((_signal("c"),))
    pipeline = SignalsPipeline({"sources": (source_one, source_two)})

    result = pipeline.collect(_normalized("addr 2"))
    assert [signal.code for signal in result] == ["a", "b", "c"]


def test_pipeline_requires_sources():
    try:
        SignalsPipeline({"sources": []})
    except ValueError:
        pass
    else:
        raise AssertionError("ValueError expected for empty sources")
