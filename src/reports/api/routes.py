"""HTTP-роуты для работы с отчётами."""

from __future__ import annotations

from uuid import UUID

from fastapi import APIRouter, HTTPException

from reports.api.schemas import (
    CreateReportIn,
    CreateReportOut,
    ReportOut,
    ReportPayloadAddressOut,
    ReportPayloadMetaOut,
    ReportPayloadOut,
    ReportPayloadRiskOut,
    ReportPayloadSignalOut,
)
from reports.application.services.payments_stub import PaymentsServiceStub
from reports.application.use_cases.create_report import CreateReportUseCase
from reports.application.use_cases.get_report import GetReportUseCase
from reports.domain.entities.report import Report
from reports.domain.exceptions.report import (
    CheckResultNotFoundError,
    ReportNotFoundError,
)
from shared.kernel.repositories import check_results_repo, reports_repo

router = APIRouter()
payments_service = PaymentsServiceStub()


@router.post('/reports', response_model=CreateReportOut)
def create_report(payload: CreateReportIn) -> CreateReportOut:
    """Создать отчёт по ранее выполненной проверке."""

    use_case = CreateReportUseCase(
        check_results_repo=check_results_repo,
        reports_repo=reports_repo,
        payments_service=payments_service,
    )
    try:
        report = use_case.execute(payload.check_id, payload.modules)
    except CheckResultNotFoundError as exc:
        raise HTTPException(status_code=404, detail='check not found') from exc

    return CreateReportOut(report_id=report.id, status=report.status)


@router.get('/reports/{report_id}', response_model=ReportOut)
def get_report(report_id: UUID) -> ReportOut:
    """Вернуть ранее сгенерированный отчёт."""

    use_case = GetReportUseCase(reports_repo=reports_repo)
    try:
        report = use_case.execute(report_id)
    except ReportNotFoundError as exc:
        raise HTTPException(status_code=404, detail='report not found') from exc

    return _to_schema(report)


def _to_schema(report: Report) -> ReportOut:
    """Преобразовать доменный отчёт в схему ответа."""

    payload = report.payload
    address = ReportPayloadAddressOut(
        raw=payload.address.raw,
        normalized=payload.address.normalized,
        confidence=payload.address.confidence,
        source=payload.address.source,
    )
    risk = ReportPayloadRiskOut(
        score=payload.risk.score,
        level=payload.risk.level,
        summary=payload.risk.summary,
    )
    signals = [
        ReportPayloadSignalOut(
            code=signal.code,
            title=signal.title,
            description=signal.description,
            severity=signal.severity,
        )
        for signal in payload.signals
    ]
    meta = ReportPayloadMetaOut(
        check_id=payload.generated_from.check_id,
        generated_at=payload.generated_from.generated_at,
    )
    payload_out = ReportPayloadOut(
        title=payload.title,
        summary=payload.summary,
        address=address,
        risk=risk,
        signals=signals,
        disclaimers=list(payload.disclaimers),
        generated_from=meta,
    )
    return ReportOut(
        report_id=report.id,
        check_id=report.check_id,
        status=report.status,
        created_at=report.created_at,
        modules=list(report.modules),
        payload=payload_out,
    )
