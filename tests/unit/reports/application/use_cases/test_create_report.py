"""Тесты use-case создания отчёта."""

from datetime import UTC, datetime
from uuid import UUID

import pytest

from checks.domain.entities.check_result import CheckResultSnapshot
from checks.domain.value_objects.address import (
    normalize_address,
    normalize_address_raw,
)
from checks.infrastructure.check_results_repo_inmemory import (
    InMemoryCheckResultsRepo,
)
from reports.application.services.payments_stub import PaymentsServiceStub
from reports.application.use_cases.create_report import CreateReportUseCase
from reports.domain.entities.report import Report
from reports.domain.exceptions.report import CheckResultNotFoundError
from reports.infrastructure.reports_repo_inmemory import (
    InMemoryReportsRepo,
)
from risks.application.scoring import build_risk_card

pytestmark = pytest.mark.asyncio


async def _snapshot(
    raw: str = 'ул мира 7',
) -> tuple[InMemoryCheckResultsRepo, UUID]:
    repo = InMemoryCheckResultsRepo()
    normalized = normalize_address(normalize_address_raw(raw))
    snapshot = CheckResultSnapshot(
        raw_input=raw,
        normalized_address=normalized,
        signals=[],
        risk_card=build_risk_card(()),
        created_at=datetime.now(UTC),
    )
    check_id = await repo.save(snapshot)
    return repo, check_id


async def test_create_report_not_found_check() -> None:
    """Если check_id неизвестен, бросаем ошибку."""

    repo = InMemoryCheckResultsRepo()
    reports_repo = InMemoryReportsRepo()
    use_case = CreateReportUseCase(
        check_results_repo=repo,
        reports_repo=reports_repo,
        payments_service=PaymentsServiceStub(),
    )

    with pytest.raises(CheckResultNotFoundError):
        await use_case.execute(UUID(int=0), ['base_summary'])


async def test_create_report_success() -> None:
    """Отчёт создаётся и содержит ссылки на исходные данные."""

    repo, check_id = await _snapshot()
    reports_repo = InMemoryReportsRepo()
    use_case = CreateReportUseCase(
        check_results_repo=repo,
        reports_repo=reports_repo,
        payments_service=PaymentsServiceStub(),
    )

    report = await use_case.execute(check_id, ['base_summary'])
    snapshot = await repo.get(check_id)
    assert snapshot is not None

    assert isinstance(report, Report)
    assert report.status == 'ready'
    assert report.payload.meta.check_id == check_id
    assert report.payload.meta.modules[0] == 'base_summary'
    assert 'base_summary' in report.payload.sections
