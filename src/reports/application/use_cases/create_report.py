"""Use-case создания отчёта по результату проверки адреса."""

from __future__ import annotations

from collections.abc import Sequence
from datetime import UTC, datetime
from uuid import UUID, uuid4

from checks.application.ports.checks import CheckResultsRepoPort
from checks.domain.entities.check_result import CheckResultSnapshot
from reports.application.ports.repos import ReportsRepoPort
from reports.application.services.payments_stub import PaymentsServiceStub
from reports.domain.entities.report import (
    Report,
    ReportPayload,
    ReportPayloadAddress,
    ReportPayloadMeta,
    ReportPayloadRisk,
    ReportPayloadSignal,
)
from reports.domain.exceptions.report import CheckResultNotFoundError

DEFAULT_DISCLAIMERS: Sequence[str] = (
    'Отчёт носит информационный характер и не является офертой.',
    'Оценка риска не является юридической гарантией.',
    'Источники данных могут содержать ошибки.',
)


class CreateReportUseCase:
    """Создание отчёта по сохранённому результату проверки."""

    __slots__ = (
        '_check_results_repo',
        '_reports_repo',
        '_payments_service',
    )

    def __init__(
        self,
        check_results_repo: CheckResultsRepoPort,
        reports_repo: ReportsRepoPort,
        payments_service: PaymentsServiceStub,
    ) -> None:
        """Сохранить зависимости use-case."""

        self._check_results_repo = check_results_repo
        self._reports_repo = reports_repo
        self._payments_service = payments_service

    def execute(self, check_id: UUID, modules: list[str]) -> Report:
        """Создать отчёт по сохранённому результату проверки."""

        snapshot = self._check_results_repo.get(check_id)
        if snapshot is None:
            raise CheckResultNotFoundError(str(check_id))

        modules_list = modules or ['base']
        self._payments_service.authorize(check_id, modules_list)
        created_at = datetime.now(UTC)
        payload = self._build_payload(snapshot, check_id, created_at)
        report = Report(
            id=uuid4(),
            check_id=check_id,
            created_at=created_at,
            status='ready',
            modules=list(modules_list),
            payload=payload,
        )
        self._reports_repo.save(report)
        return report

    @staticmethod
    def _build_payload(
        snapshot: CheckResultSnapshot,
        check_id: UUID,
        generated_at: datetime,
    ) -> ReportPayload:
        """Построить полезную нагрузку отчёта."""

        normalized = snapshot.normalized_address
        risk_card = snapshot.risk_card
        signals = [
            ReportPayloadSignal(
                code=signal.code,
                title=signal.title,
                description=signal.description,
                severity=int(signal.severity),
            )
            for signal in snapshot.signals
        ]
        address_block = ReportPayloadAddress(
            raw=snapshot.raw_input,
            normalized=normalized.normalized,
            confidence=normalized.confidence,
            source=normalized.source,
        )
        risk_block = ReportPayloadRisk(
            score=risk_card.score,
            level=risk_card.level.value,
            summary=risk_card.summary,
        )
        meta = ReportPayloadMeta(
            check_id=check_id,
            generated_at=generated_at,
        )
        return ReportPayload(
            title='Отчёт по адресу',
            summary=risk_card.summary,
            address=address_block,
            risk=risk_block,
            signals=signals,
            disclaimers=list(DEFAULT_DISCLAIMERS),
            generated_from=meta,
        )
