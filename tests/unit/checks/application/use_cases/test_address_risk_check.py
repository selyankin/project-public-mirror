"""Тесты AddressRiskCheckUseCase."""

from checks.adapters.address_resolver_stub import AddressResolverStub
from checks.adapters.signals_provider_stub import SignalsProviderStub
from checks.application.use_cases.address_risk_check import (
    AddressRiskCheckUseCase,
)
from checks.domain.value_objects.address import normalize_address_raw


def test_risk_check_use_case_produces_confidence_signal() -> None:
    """Новый use-case возвращает сигналы и риск-карту."""

    resolver = AddressResolverStub({})
    signals_provider = SignalsProviderStub({})
    use_case = AddressRiskCheckUseCase(
        address_resolver=resolver,
        signals_provider=signals_provider,
    )

    raw = normalize_address_raw('г. Москва')
    result = use_case.execute(raw)

    assert result.normalized_address.normalized.startswith('г.')
    codes = [signal.code for signal in result.signals]
    assert 'address_confidence_low' in codes
    assert 0 <= result.risk_card.score <= 100
