import pytest
from risks.domain.constants.enums.risk import SignalSeverity
from risks.domain.signals_catalog import (
    all_signal_definitions,
    get_signal_definition,
)


def test_get_signal_definition_returns_definition():
    definition = get_signal_definition('address_incomplete')
    assert definition.title == 'Incomplete address'
    assert definition.severity is SignalSeverity.medium


def test_get_signal_definition_unknown_code():
    with pytest.raises(KeyError):
        get_signal_definition('unknown')


def test_all_signal_definitions_order():
    definitions = all_signal_definitions()
    assert isinstance(definitions, tuple)
    assert [definition.code for definition in definitions] == [
        'address_incomplete',
        'possible_apartments',
        'hostel_keyword',
        'residential_complex_hint',
        'url_not_supported_yet',
        'query_type_not_supported',
        'query_not_address_like',
    ]


def test_signal_definition_to_dict():
    definition = get_signal_definition('hostel_keyword')
    data = definition.to_dict()
    assert data['code'] == 'hostel_keyword'
    assert data['severity'] == int(SignalSeverity.high)
