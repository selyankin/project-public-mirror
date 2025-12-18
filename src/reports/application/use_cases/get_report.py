"""Use-case получения отчёта по идентификатору."""

from __future__ import annotations

from uuid import UUID

from reports.application.ports.repos import ReportsRepoPort
from reports.domain.entities.report import Report
from reports.domain.exceptions.report import ReportNotFoundError


class GetReportUseCase:
    """Возвращает сохранённый отчёт."""

    __slots__ = ('_reports_repo',)

    def __init__(self, reports_repo: ReportsRepoPort) -> None:
        """Сохранить ссылку на репозиторий."""

        self._reports_repo = reports_repo

    async def execute(self, report_id: UUID) -> Report:
        """Вернуть отчёт или возбуждать ошибку, если он не найден."""

        report = await self._reports_repo.get(report_id)
        if report is None:
            raise ReportNotFoundError(str(report_id))
        return report
