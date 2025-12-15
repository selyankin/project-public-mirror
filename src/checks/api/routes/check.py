"""API routes for address checks and risk cards."""

from __future__ import annotations

from fastapi import APIRouter, HTTPException

from src.checks.adapters.address_resolver_stub import AddressResolverStub
from src.checks.adapters.signals_provider_stub import SignalsProviderStub
from src.checks.application.use_cases.check_address import CheckAddressUseCase
from src.checks.domain.value_objects.address import AddressValidationError
from src.checks.presentation.api.v1.serialization.input.checks import CheckIn
from src.checks.presentation.api.v1.serialization.output.checks import (
    RiskCardOut,
)

router = APIRouter()


@router.post('/check', response_model=RiskCardOut)
def check_address(payload: CheckIn) -> RiskCardOut:
    """Run address check and return RiskCard."""

    address_resolver = AddressResolverStub({})
    signals_provider = SignalsProviderStub({})
    use_case = CheckAddressUseCase(
        address_resolver,
        signals_provider,
    )

    try:
        result = use_case.execute(payload.address)
    except AddressValidationError as exc:
        raise HTTPException(status_code=422, detail=str(exc)) from exc

    return RiskCardOut(**result)
