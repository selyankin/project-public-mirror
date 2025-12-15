import pytest

from src.checks.adapters.address_resolver_stub import AddressResolverStub
from src.checks.adapters.signals_provider_stub import SignalsProviderStub
from src.checks.application.use_cases.check_address import (
    CheckAddressUseCase,
)
from src.checks.domain.value_objects.address import AddressValidationError


def make_use_case():
    address_resolver = AddressResolverStub({})
    signals_provider = SignalsProviderStub({})
    return CheckAddressUseCase(address_resolver, signals_provider)


def test_execute_returns_risk_card_dict():
    use_case = make_use_case()
    result = use_case.execute("ул мира 7")
    assert isinstance(result, dict)
    assert result["score"] >= 0
    assert "level" in result
    assert isinstance(result["signals"], list)


def test_execute_detects_apartments_signal():
    use_case = make_use_case()
    result = use_case.execute("ул мира 7 апарт")
    assert any(
        sig["code"] == "possible_apartments" for sig in result["signals"]
    )


def test_execute_raises_domain_error_for_empty_string():
    use_case = make_use_case()
    with pytest.raises(AddressValidationError):
        use_case.execute("   ")
