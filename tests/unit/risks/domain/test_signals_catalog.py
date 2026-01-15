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
        'address_confidence_unknown',
        'address_confidence_low',
        'address_source_stub',
        'url_not_supported_yet',
        'query_type_not_supported',
        'query_not_address_like',
        'kad_arbitr_has_bankruptcy_cases',
        'kad_arbitr_many_cases_last_12m',
        'kad_arbitr_mostly_defendant',
        'kad_arbitr_no_cases_found',
        'kad_arbitr_losses_last_24m',
        'kad_arbitr_bankruptcy_procedure',
        'kad_arbitr_many_loses_as_defendant',
        'kad_arbitr_outcome_unknown_many',
        'kad_arbitr_source_blocked',
        'kad_arbitr_source_error',
        'kad_arbitr_participant_not_found',
    ]


def test_signal_definition_to_dict():
    definition = get_signal_definition('hostel_keyword')
    data = definition.to_dict()
    assert data['code'] == 'hostel_keyword'
    assert data['severity'] == int(SignalSeverity.high)
