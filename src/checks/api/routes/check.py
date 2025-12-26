"""API маршруты для проверки адресов и URL."""

from __future__ import annotations

from typing import Any

from fastapi import APIRouter, HTTPException, Request
from fastapi.responses import JSONResponse

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
from checks.infrastructure.listing_resolver_factory import (
    build_listing_resolver_use_case,
)
from checks.presentation.api.v1.serialization.input.checks import (
    CheckIn,
    LegacyCheckIn,
)
from checks.presentation.api.v1.serialization.output.checks import RiskCardOut
from shared.kernel.repositories import check_cache_repo, check_results_repo
from shared.kernel.settings import get_settings

router = APIRouter()


def _build_use_case(request: Request) -> CheckAddressUseCase:
    """Создать use-case с тестовыми адаптерами."""
    settings = get_settings()
    address_resolver = build_address_resolver(settings)
    signals_provider = SignalsProviderStub({})
    fias_client = getattr(request.app.state, 'fias_client', None)
    listing_resolver_use_case = build_listing_resolver_use_case()

    if fias_client is None:
        raise RuntimeError('FIAS client is not configured.')

    address_risk_use_case = AddressRiskCheckUseCase(
        address_resolver=address_resolver,
        signals_provider=signals_provider,
    )

    return CheckAddressUseCase(
        address_risk_check_use_case=address_risk_use_case,
        check_results_repo=check_results_repo,
        check_cache_repo=check_cache_repo,
        fias_client=fias_client,
        listing_resolver_use_case=listing_resolver_use_case,
        fias_mode=settings.FIAS_MODE,
        cache_version=settings.CHECK_CACHE_VERSION,
    )


def _encode_response(payload: dict[str, Any]) -> JSONResponse:
    """Валидировать и сериализовать ответ без лишних полей."""

    response = RiskCardOut(**payload)
    data = response.model_dump(mode='json')
    if data.get('fias') is None:
        data.pop('fias', None)
    return JSONResponse(content=data)


@router.post('/check', response_model=RiskCardOut)
async def check(payload: CheckIn, request: Request) -> JSONResponse:
    """Выполнить проверку по унифицированному запросу."""

    use_case = _build_use_case(request)
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

    return _encode_response(result)


@router.post('/check/address', response_model=RiskCardOut)
async def check_address(
    payload: LegacyCheckIn,
    request: Request,
) -> JSONResponse:
    """Выполнить проверку по устаревшему адресу."""

    use_case = _build_use_case(request)
    try:
        result = await use_case.execute(payload.address)

    except AddressValidationError as exc:
        raise HTTPException(status_code=422, detail=str(exc)) from exc

    return _encode_response(result)
