"""Проверка идемпотентности CheckAddressUseCase."""

from datetime import UTC, datetime, timedelta

from checks.application.use_cases.address_risk_check import (
    AddressRiskCheckResult,
)
from checks.application.use_cases.check_address import (
    CheckAddressUseCase,
)
from checks.domain.value_objects.address import (
    normalize_address,
    normalize_address_raw,
)
from checks.domain.value_objects.query import CheckQuery
from checks.infrastructure.check_cache_repo_inmemory import (
    InMemoryCheckCacheRepo,
)
from checks.infrastructure.check_results_repo_inmemory import (
    InMemoryCheckResultsRepo,
)
from risks.application.scoring import build_risk_card


class DummyClock:
    """Управляемые часы для проверки TTL."""

    def __init__(self) -> None:
        self.value = datetime(2024, 1, 1, tzinfo=UTC)

    def advance(self, seconds: int) -> None:
        """Сместить время вперёд."""

        self.value += timedelta(seconds=seconds)

    def __call__(self) -> datetime:
        """Вернуть текущие тестовые часы."""

        return self.value


class FakeAddressRiskCheckUseCase:
    """Ставит счётчик вызовов."""

    def __init__(self) -> None:
        normalized = normalize_address(normalize_address_raw('ул мира 7'))
        self._result = AddressRiskCheckResult(
            normalized_address=normalized,
            signals=[],
            risk_card=build_risk_card(()),
        )
        self.calls = 0

    def execute(self, raw):
        self.calls += 1
        return self._result


def test_idempotent_behavior_returns_same_check_id() -> None:
    """Повторный запрос в пределах TTL не вызывает риск-движок."""

    clock = DummyClock()
    fake_risk = FakeAddressRiskCheckUseCase()
    use_case = CheckAddressUseCase(
        address_risk_check_use_case=fake_risk,
        check_results_repo=InMemoryCheckResultsRepo(),
        check_cache_repo=InMemoryCheckCacheRepo(ttl_seconds=600, now_fn=clock),
        fias_mode='stub',
        cache_version='test',
    )

    query = CheckQuery({'type': 'address', 'query': 'ул мира 7'})
    first = use_case.execute_query(query)
    second = use_case.execute_query(query)

    assert fake_risk.calls == 1
    assert first['check_id'] == second['check_id']


def test_cache_expires_after_ttl() -> None:
    """После истечения TTL проверка выполняется повторно."""

    clock = DummyClock()
    fake_risk = FakeAddressRiskCheckUseCase()
    use_case = CheckAddressUseCase(
        address_risk_check_use_case=fake_risk,
        check_results_repo=InMemoryCheckResultsRepo(),
        check_cache_repo=InMemoryCheckCacheRepo(ttl_seconds=1, now_fn=clock),
        fias_mode='stub',
        cache_version='test',
    )

    query = CheckQuery({'type': 'address', 'query': 'ул мира 7'})
    first = use_case.execute_query(query)
    clock.advance(2)
    second = use_case.execute_query(query)

    assert fake_risk.calls == 2
    assert first['check_id'] != second['check_id']
