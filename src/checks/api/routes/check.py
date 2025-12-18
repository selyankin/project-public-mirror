"""API маршруты для проверки адресов и URL."""

from __future__ import annotations

from fastapi import APIRouter, HTTPException

from checks.adapters.signals_provider_stub import SignalsProviderStub
from checks.application.use_cases.address_risk_check import (
    AddressRiskCheckUseCase,
)
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
from shared.kernel.repositories import check_cache_repo, check_results_repo
from shared.kernel.settings import get_settings

router = APIRouter()


def _build_use_case() -> CheckAddressUseCase:
    """Создать use-case с тестовыми адаптерами."""
    settings = get_settings()
    address_resolver = build_address_resolver(settings)
    signals_provider = SignalsProviderStub({})
    address_risk_use_case = AddressRiskCheckUseCase(
        address_resolver=address_resolver,
        signals_provider=signals_provider,
    )

    return CheckAddressUseCase(
        address_risk_check_use_case=address_risk_use_case,
        check_results_repo=check_results_repo,
        check_cache_repo=check_cache_repo,
        fias_mode=settings.FIAS_MODE,
        cache_version=settings.CHECK_CACHE_VERSION,
    )


@router.post('/check', response_model=RiskCardOut)
async def check(payload: CheckIn) -> RiskCardOut:
    """Выполнить проверку по унифицированному запросу."""

    use_case = _build_use_case()
    try:
        query = CheckQuery(
            {
                'type': payload.type,
                'query': payload.query,
            }
        )
        result = await use_case.execute_query(query)

    except (QueryInputError, AddressValidationError, ValueError) as exc:
        raise HTTPException(status_code=422, detail=str(exc)) from exc

    return RiskCardOut(**result)


@router.post('/check/address', response_model=RiskCardOut)
async def check_address(payload: LegacyCheckIn) -> RiskCardOut:
    """Выполнить проверку по устаревшему адресу."""

    use_case = _build_use_case()
    try:
        result = await use_case.execute(payload.address)

    except AddressValidationError as exc:
        raise HTTPException(status_code=422, detail=str(exc)) from exc

    return RiskCardOut(**result)
