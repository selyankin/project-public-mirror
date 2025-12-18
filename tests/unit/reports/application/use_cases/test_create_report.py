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


def _snapshot(raw: str = 'ул мира 7') -> tuple[InMemoryCheckResultsRepo, UUID]:
    repo = InMemoryCheckResultsRepo()
    normalized = normalize_address(normalize_address_raw(raw))
    snapshot = CheckResultSnapshot(
        raw_input=raw,
        normalized_address=normalized,
        signals=[],
        risk_card=build_risk_card(()),
        created_at=datetime.now(UTC),
    )
    check_id = repo.save(snapshot)
    return repo, check_id


def test_create_report_not_found_check() -> None:
    """Если check_id неизвестен, бросаем ошибку."""

    repo = InMemoryCheckResultsRepo()
    reports_repo = InMemoryReportsRepo()
    use_case = CreateReportUseCase(
        check_results_repo=repo,
        reports_repo=reports_repo,
        payments_service=PaymentsServiceStub(),
    )

    with pytest.raises(CheckResultNotFoundError):
        use_case.execute(UUID(int=0), [])


def test_create_report_success() -> None:
    """Отчёт создаётся и содержит ссылки на исходные данные."""

    repo, check_id = _snapshot()
    reports_repo = InMemoryReportsRepo()
    use_case = CreateReportUseCase(
        check_results_repo=repo,
        reports_repo=reports_repo,
        payments_service=PaymentsServiceStub(),
    )

    report = use_case.execute(check_id, ['base'])
    snapshot = repo.get(check_id)
    assert snapshot is not None

    assert isinstance(report, Report)
    assert report.status == 'ready'
    assert report.payload.generated_from.check_id == check_id
    assert report.payload.risk.score == snapshot.risk_card.score
    assert len(report.payload.signals) == len(snapshot.signals)
    assert (
        report.payload.address.confidence
        == snapshot.normalized_address.confidence
    )
