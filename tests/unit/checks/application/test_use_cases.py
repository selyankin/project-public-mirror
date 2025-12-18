from uuid import uuid4

import pytest

from checks.adapters.address_resolver_stub import AddressResolverStub
from checks.adapters.signals_provider_stub import SignalsProviderStub
from checks.application.use_cases.address_risk_check import (
    AddressRiskCheckResult,
    AddressRiskCheckUseCase,
)
from checks.application.use_cases.check_address import (
    CheckAddressUseCase,
)
from checks.domain.value_objects.address import (
    AddressRaw,
    normalize_address,
    normalize_address_raw,
)
from checks.domain.value_objects.query import CheckQuery, QueryInputError
from checks.infrastructure.check_results_repo_inmemory import (
    InMemoryCheckResultsRepo,
)
from risks.application.scoring import build_risk_card


def make_use_case():
    address_resolver = AddressResolverStub({})
    signals_provider = SignalsProviderStub({})
    address_risk_use_case = AddressRiskCheckUseCase(
        address_resolver=address_resolver,
        signals_provider=signals_provider,
    )
    check_results_repo = InMemoryCheckResultsRepo()
    return CheckAddressUseCase(
        address_risk_check_use_case=address_risk_use_case,
        check_results_repo=check_results_repo,
    )


def test_execute_returns_risk_card_dict():
    use_case = make_use_case()
    result = use_case.execute('ул мира 7')
    assert isinstance(result, dict)
    assert {'score', 'level', 'signals', 'check_id'} <= result.keys()
    assert result['address_source'] == 'stub'
    assert result['address_confidence'] in (
        'exact',
        'high',
        'medium',
        'low',
        'unknown',
    )
    assert result['check_id'] is not None


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


def test_address_query_not_address_like_returns_signal():
    use_case = make_use_case()
    query = CheckQuery({'type': 'address', 'query': 'привет как дела'})
    result = use_case.execute_query(query)
    assert any(
        sig['code'] == 'query_not_address_like' for sig in result['signals']
    )


def test_address_query_keyword_only_passes():
    use_case = make_use_case()
    query = CheckQuery({'type': 'address', 'query': 'улица ленина'})
    result = use_case.execute_query(query)
    assert all(
        sig['code'] != 'query_not_address_like' for sig in result['signals']
    )


def test_execute_query_url_with_address():
    use_case = make_use_case()
    query = CheckQuery(
        {'type': 'url', 'query': 'https://x.test/?address=ул+мира+7'}
    )
    result = use_case.execute_query(query)
    assert all(
        sig['code'] != 'url_not_supported_yet' for sig in result['signals']
    )
    assert result['check_id'] is not None


def test_execute_query_url_with_non_address_text():
    use_case = make_use_case()
    query = CheckQuery(
        {
            'type': 'url',
            'query': 'https://x.test/?address=привет+как+дела',
        }
    )
    result = use_case.execute_query(query)
    assert any(
        sig['code'] == 'url_not_supported_yet' for sig in result['signals']
    )


def test_execute_query_url_without_address():
    use_case = make_use_case()
    query = CheckQuery({'type': 'url', 'query': 'https://x.test/'})
    result = use_case.execute_query(query)
    assert any(
        sig['code'] == 'url_not_supported_yet' for sig in result['signals']
    )


def test_address_path_uses_address_risk_use_case():
    normalized = normalize_address(normalize_address_raw('ул мира 7'))

    class FakeAddressRiskCheckUseCase:
        def __init__(self):
            self.called_with = None
            self._result = AddressRiskCheckResult(
                normalized_address=normalized,
                signals=[],
                risk_card=build_risk_card(()),
            )

        def execute(self, raw):
            self.called_with = raw
            return self._result

    fake = FakeAddressRiskCheckUseCase()

    class DummyRepo:
        def __init__(self):
            self.saved_snapshot = None

        def save(self, snapshot):
            self.saved_snapshot = snapshot
            return uuid4()

        def get(self, check_id):
            return None

    use_case = CheckAddressUseCase(
        address_risk_check_use_case=fake,
        check_results_repo=DummyRepo(),
    )
    query = CheckQuery({'type': 'address', 'query': 'ул мира 7'})
    result = use_case.execute_query(query)
    assert result['score'] == 0
    assert fake.called_with is not None
    assert isinstance(fake.called_with, AddressRaw)
