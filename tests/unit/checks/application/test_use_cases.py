import pytest

from src.checks.adapters.address_resolver_stub import AddressResolverStub
from src.checks.adapters.signals_provider_stub import SignalsProviderStub
from src.checks.application.use_cases.check_address import (
    CheckAddressUseCase,
)
from src.checks.domain.value_objects.query import CheckQuery, QueryInputError


def make_use_case():
    address_resolver = AddressResolverStub({})
    signals_provider = SignalsProviderStub({})
    return CheckAddressUseCase(
        address_resolver,
        signals_provider,
    )


def test_execute_returns_risk_card_dict():
    use_case = make_use_case()
    result = use_case.execute('ул мира 7')
    assert isinstance(result, dict)
    assert {'score', 'level', 'signals'} <= result.keys()


def test_execute_detects_apartments_signal():
    use_case = make_use_case()
    result = use_case.execute('ул мира 7 апарт')
    assert any(
        sig['code'] == 'possible_apartments' for sig in result['signals']
    )


def test_execute_raises_query_error_for_empty_string():
    use_case = make_use_case()
    with pytest.raises(QueryInputError):
        use_case.execute('   ')


def test_execute_query_address_path():
    use_case = make_use_case()
    query = CheckQuery({'type': 'address', 'query': 'ул мира 7'})
    result = use_case.execute_query(query)
    assert 'level' in result


def test_execute_query_url_with_address():
    use_case = make_use_case()
    query = CheckQuery(
        {'type': 'url', 'query': 'https://x.test/?address=ул+мира+7'}
    )
    result = use_case.execute_query(query)
    assert all(
        sig['code'] != 'url_not_supported_yet' for sig in result['signals']
    )


def test_execute_query_url_without_address():
    use_case = make_use_case()
    query = CheckQuery({'type': 'url', 'query': 'https://x.test/'})
    result = use_case.execute_query(query)
    assert any(
        sig['code'] == 'url_not_supported_yet' for sig in result['signals']
    )


def test_url_with_embedded_address_uses_address_flow():
    use_case = make_use_case()
    result = use_case.execute_query(
        CheckQuery(
            {
                'type': 'url',
                'query': 'https://example.com/?address=ул+мира+7',
            },
        ),
    )
    assert all(
        signal['code'] != 'url_not_supported_yet'
        for signal in result['signals']
    )


def test_url_without_address_returns_placeholder_signal():
    use_case = make_use_case()
    result = use_case.execute_query(
        CheckQuery(
            {
                'type': 'url',
                'query': 'https://example.com/',
            },
        ),
    )
    assert any(
        signal['code'] == 'url_not_supported_yet'
        for signal in result['signals']
    )
