"""API маршруты для проверки адресов и URL."""

from __future__ import annotations

import inspect
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
from checks.presentation.api.v1.serialization.input.checks import (
    CheckIn,
    LegacyCheckIn,
)
from checks.presentation.api.v1.serialization.output.checks import RiskCardOut
from shared.kernel.kad_arbitr_client_factory import build_kad_arbitr_client
from shared.kernel.repositories import check_cache_repo, check_results_repo
from shared.kernel.settings import get_settings
from sources.kad_arbitr.use_cases.resolve_cases_for_participant import (
    ResolveKadArbitrCasesForParticipant,
)

router = APIRouter()


def _build_use_case(request: Request) -> CheckAddressUseCase:
    """Создать use-case с тестовыми адаптерами."""
    settings = get_settings()
    address_resolver = build_address_resolver(settings)
    signals_provider = SignalsProviderStub({})
    fias_client = getattr(request.app.state, 'fias_client', None)

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
        fias_mode=settings.FIAS_MODE,
        cache_version=settings.CHECK_CACHE_VERSION,
        settings=settings,
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


@router.get('/internal/kad-arbitr/search')
async def internal_kad_arbitr_search(
    participant: str,
    participant_type: int | None = None,
    max_pages: int = 2,
) -> dict[str, Any]:
    """Выполнить ручной запрос kad.arbitr.ru."""

    settings = get_settings()
    client = build_kad_arbitr_client(settings=settings)
    resolver = ResolveKadArbitrCasesForParticipant(client=client)
    try:
        result = await resolver.execute(
            participant=participant,
            participant_type=participant_type,
            max_pages=max_pages,
        )
    finally:
        close_method = getattr(client, 'close', None)
        if callable(close_method):
            result_close = close_method()
            if inspect.isawaitable(result_close):
                await result_close

    return {
        'participant': participant,
        'total': result.total,
        'cases': [
            {
                'case_id': case.case_id,
                'case_number': case.case_number,
                'court': case.court,
                'case_type': case.case_type,
                'start_date': (
                    case.start_date.isoformat() if case.start_date else None
                ),
                'url': case.url,
            }
            for case in result.cases
        ],
        'signals': [signal.to_dict() for signal in result.signals],
    }
