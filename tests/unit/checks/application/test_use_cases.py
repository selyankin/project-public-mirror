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
from checks.infrastructure.check_cache_repo_inmemory import (
    InMemoryCheckCacheRepo,
)
from checks.infrastructure.check_results_repo_inmemory import (
    InMemoryCheckResultsRepo,
)
from checks.infrastructure.fias.client_stub import StubFiasClient
from risks.application.scoring import build_risk_card

pytestmark = pytest.mark.asyncio


def make_use_case(fias_client: StubFiasClient | None = None):
    address_resolver = AddressResolverStub({})
    signals_provider = SignalsProviderStub({})
    address_risk_use_case = AddressRiskCheckUseCase(
        address_resolver=address_resolver,
        signals_provider=signals_provider,
    )
    check_results_repo = InMemoryCheckResultsRepo()
    check_cache_repo = InMemoryCheckCacheRepo(ttl_seconds=600)
    return CheckAddressUseCase(
        address_risk_check_use_case=address_risk_use_case,
        check_results_repo=check_results_repo,
        check_cache_repo=check_cache_repo,
        fias_client=fias_client or StubFiasClient(),
        fias_mode='stub',
        cache_version='test',
    )


async def test_execute_returns_risk_card_dict():
    use_case = make_use_case()
    result = await use_case.execute('ул мира 7')
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
    assert 'fias' not in result


async def test_execute_detects_apartments_signal():
    use_case = make_use_case()
    result = await use_case.execute('ул мира 7 апарт')
    assert any(
        sig['code'] == 'possible_apartments' for sig in result['signals']
    )


async def test_execute_raises_query_error_for_empty_string():
    use_case = make_use_case()
    with pytest.raises(QueryInputError):
        await use_case.execute('   ')


async def test_execute_query_address_path():
    use_case = make_use_case()
    query = CheckQuery({'type': 'address', 'query': 'ул мира 7'})
    result = await use_case.execute_query(query)
    assert 'level' in result


async def test_address_query_not_address_like_returns_signal():
    use_case = make_use_case()
    query = CheckQuery({'type': 'address', 'query': 'привет как дела'})
    result = await use_case.execute_query(query)
    assert any(
        sig['code'] == 'query_not_address_like' for sig in result['signals']
    )


async def test_address_query_keyword_only_passes():
    use_case = make_use_case()
    query = CheckQuery({'type': 'address', 'query': 'улица ленина'})
    result = await use_case.execute_query(query)
    assert all(
        sig['code'] != 'query_not_address_like' for sig in result['signals']
    )


async def test_execute_query_url_with_address():
    use_case = make_use_case()
    query = CheckQuery(
        {'type': 'url', 'query': 'https://x.test/?address=ул+мира+7'}
    )
    result = await use_case.execute_query(query)
    assert all(
        sig['code'] != 'url_not_supported_yet' for sig in result['signals']
    )
    assert result['check_id'] is not None


async def test_execute_query_url_with_non_address_text():
    use_case = make_use_case()
    query = CheckQuery(
        {
            'type': 'url',
            'query': 'https://x.test/?address=привет+как+дела',
        }
    )
    result = await use_case.execute_query(query)
    assert any(
        sig['code'] == 'url_not_supported_yet' for sig in result['signals']
    )


async def test_execute_query_url_without_address():
    use_case = make_use_case()
    query = CheckQuery({'type': 'url', 'query': 'https://x.test/'})
    result = await use_case.execute_query(query)
    assert any(
        sig['code'] == 'url_not_supported_yet' for sig in result['signals']
    )


async def test_address_path_uses_address_risk_use_case():
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

        async def save(self, snapshot):
            self.saved_snapshot = snapshot
            return uuid4()

        async def get(self, check_id):
            return None

    class DummyCacheRepo:
        async def get(self, key):
            return None

        async def set(self, key, check_id):
            return None

        async def cleanup(self):
            return None

    use_case = CheckAddressUseCase(
        address_risk_check_use_case=fake,
        check_results_repo=DummyRepo(),
        check_cache_repo=DummyCacheRepo(),
        fias_client=StubFiasClient(),
        fias_mode='stub',
        cache_version='test',
    )
    query = CheckQuery({'type': 'address', 'query': 'ул мира 7'})
    result = await use_case.execute_query(query)
    assert result['score'] == 0
    assert fake.called_with is not None
    assert isinstance(fake.called_with, AddressRaw)


async def test_address_path_includes_fias_payload_when_stub_matches():
    """Если ФИАС нашёл адрес, ответ содержит блок fias."""

    use_case = make_use_case()
    result = await use_case.execute('г. Москва, ул. Тверская, д. 1')
    fias_payload = result.get('fias')
    assert fias_payload is not None
    assert fias_payload['fias_id'] == 'moscow-001'
    assert 'normalized' in fias_payload


async def test_address_path_without_match_has_no_fias_block():
    """Если ФИАС не дал результат, поле fias отсутствует."""

    use_case = make_use_case()
    result = await use_case.execute('ул мира 7')
    assert 'fias' not in result


async def test_url_path_propagates_fias_payload_after_extraction():
    """URL-вход при извлечении адреса также обогащается fias."""

    use_case = make_use_case()
    query = CheckQuery(
        {
            'type': 'url',
            'query': 'https://x.test/?address=г.+Москва,+ул.+Тверская',
        }
    )
    result = await use_case.execute_query(query)
    fias_payload = result.get('fias')
    assert fias_payload is not None
    assert fias_payload['normalized'].startswith('г. москва')
