import pytest

from src.risks.domain.constants.enums.risk import SignalSeverity
from src.risks.domain.helpers.signals import (
    all_signal_definitions,
    get_signal_definition,
)


def test_get_signal_definition_returns_definition():
    definition = get_signal_definition("address_incomplete")
    assert definition.title == "Incomplete address"
    assert definition.severity is SignalSeverity.medium


def test_get_signal_definition_unknown_code():
    with pytest.raises(KeyError):
        get_signal_definition("unknown")


def test_all_signal_definitions_order():
    definitions = all_signal_definitions()
    assert isinstance(definitions, tuple)
    assert [definition.code for definition in definitions] == [
        "address_incomplete",
        "possible_apartments",
        "hostel_keyword",
        "residential_complex_hint",
    ]


def test_signal_definition_to_dict():
    definition = get_signal_definition("hostel_keyword")
    data = definition.to_dict()
    assert data["code"] == "hostel_keyword"
    assert data["severity"] == int(SignalSeverity.high)
