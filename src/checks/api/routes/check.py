"""API маршруты для проверки адресов и URL."""

from __future__ import annotations

from checks.adapters.signals_provider_stub import SignalsProviderStub
from checks.application.use_cases.check_address import CheckAddressUseCase
from checks.domain.value_objects.address import AddressValidationError
from checks.domain.value_objects.query import CheckQuery, QueryInputError
from checks.infrastructure.address_resolver_factory import (
    build_address_resolver,
)
from checks.presentation.api.v1.serialization.input.checks import (
    CheckIn,
    LegacyCheckIn,
)
from checks.presentation.api.v1.serialization.output.checks import RiskCardOut
from fastapi import APIRouter, HTTPException
from shared.kernel.settings import get_settings

router = APIRouter()


def _build_use_case() -> CheckAddressUseCase:
    """Создать use-case с тестовыми адаптерами."""
    settings = get_settings()
    address_resolver = build_address_resolver(settings)
    signals_provider = SignalsProviderStub({})

    return CheckAddressUseCase(
        address_resolver,
        signals_provider,
    )


@router.post('/check', response_model=RiskCardOut)
def check(payload: CheckIn) -> RiskCardOut:
    """Выполнить проверку по унифицированному запросу."""

    use_case = _build_use_case()
    try:
        query = CheckQuery(
            {
                'type': payload.type,
                'query': payload.query,
            }
        )
        result = use_case.execute_query(query)

    except (QueryInputError, AddressValidationError, ValueError) as exc:
        raise HTTPException(status_code=422, detail=str(exc)) from exc

    return RiskCardOut(**result)


@router.post('/check/address', response_model=RiskCardOut)
def check_address(payload: LegacyCheckIn) -> RiskCardOut:
    """Выполнить проверку по устаревшему адресу."""

    use_case = _build_use_case()
    try:
        result = use_case.execute(payload.address)

    except AddressValidationError as exc:
        raise HTTPException(status_code=422, detail=str(exc)) from exc

    return RiskCardOut(**result)
