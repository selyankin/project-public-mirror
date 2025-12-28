"""Unit-тесты use-case разрешения Росреестра."""

import pytest

from sources.rosreestr.dto import RosreestrApiResponse
from sources.rosreestr.exceptions import RosreestrBadResponseError
from sources.rosreestr.stub_client import StubRosreestrClient
from sources.rosreestr.use_cases.resolve_house_by_cadastral import (
    ResolveRosreestrHouseByCadastralUseCase,
)


def test_resolve_returns_normalized_object_for_known_cadastral():
    use_case = ResolveRosreestrHouseByCadastralUseCase(
        client=StubRosreestrClient(),
    )
    result = use_case.execute(cadastral_number='77:01:000101:1')
    assert result is not None
    assert result.cad_number == '77:01:000101:1'


def test_resolve_returns_none_when_not_found():
    use_case = ResolveRosreestrHouseByCadastralUseCase(
        client=StubRosreestrClient(),
    )
    assert use_case.execute(cadastral_number='77:01:999999:9') is None


def test_resolve_raises_value_error_on_invalid_cadastral():
    use_case = ResolveRosreestrHouseByCadastralUseCase(
        client=StubRosreestrClient(),
    )
    with pytest.raises(ValueError):
        use_case.execute(cadastral_number='invalid')


def test_resolve_raises_bad_response_on_status_error():
    class FailingClient(StubRosreestrClient):
        def get_object(
            self,
            *,
            cadastral_number: str,
        ) -> RosreestrApiResponse:
            return RosreestrApiResponse(status=500, found=False, object=None)

    use_case = ResolveRosreestrHouseByCadastralUseCase(client=FailingClient())
    with pytest.raises(RosreestrBadResponseError):
        use_case.execute(cadastral_number='77:01:000101:1')
