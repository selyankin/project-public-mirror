"""HTTP-роуты для работы с отчётами."""

from __future__ import annotations

from uuid import UUID

from fastapi import APIRouter, HTTPException

from reports.api.schemas import (
    CreateReportIn,
    CreateReportOut,
    ReportOut,
    ReportPayloadMetaOut,
    ReportPayloadOut,
)
from reports.application.services.module_builders import (
    DEFAULT_MODULE_BUILDERS,
)
from reports.application.services.payments_stub import PaymentsServiceStub
from reports.application.services.report_assembler import ReportAssembler
from reports.application.use_cases.create_report import CreateReportUseCase
from reports.application.use_cases.get_report import GetReportUseCase
from reports.domain.entities.report import Report
from reports.domain.exceptions.report import (
    CheckResultNotFoundError,
    ReportInvalidModulesError,
    ReportModuleError,
    ReportModuleNotFoundError,
    ReportModulePaymentRequiredError,
    ReportNotFoundError,
)
from shared.kernel.repositories import check_results_repo, reports_repo

router = APIRouter()
payments_service = PaymentsServiceStub()
report_assembler = ReportAssembler(DEFAULT_MODULE_BUILDERS)


@router.post('/reports', response_model=CreateReportOut)
async def create_report(payload: CreateReportIn) -> CreateReportOut:
    """Создать отчёт по ранее выполненной проверке."""

    use_case = CreateReportUseCase(
        check_results_repo=check_results_repo,
        reports_repo=reports_repo,
        payments_service=payments_service,
        report_assembler=report_assembler,
    )
    try:
        report = await use_case.execute(payload.check_id, payload.modules)
    except CheckResultNotFoundError as exc:
        raise HTTPException(status_code=404, detail='check not found') from exc
    except ReportModuleNotFoundError as exc:
        raise HTTPException(
            status_code=400,
            detail=_module_error_detail(str(exc), exc.module_ids),
        ) from exc
    except ReportInvalidModulesError as exc:
        raise HTTPException(
            status_code=400,
            detail=_module_error_detail(str(exc), exc.module_ids),
        ) from exc
    except ReportModulePaymentRequiredError as exc:
        raise HTTPException(
            status_code=402,
            detail=_module_error_detail(str(exc), exc.module_ids),
        ) from exc
    except ReportModuleError as exc:
        raise HTTPException(
            status_code=400,
            detail=_module_error_detail(
                str(exc), getattr(exc, 'module_ids', [])
            ),
        ) from exc

    return CreateReportOut(report_id=report.id, status=report.status)


@router.get('/reports/{report_id}', response_model=ReportOut)
async def get_report(report_id: UUID) -> ReportOut:
    """Вернуть ранее сгенерированный отчёт."""

    use_case = GetReportUseCase(reports_repo=reports_repo)
    try:
        report = await use_case.execute(report_id)
    except ReportNotFoundError as exc:
        raise HTTPException(status_code=404, detail='report not found') from exc

    return _to_schema(report)


def _to_schema(report: Report) -> ReportOut:
    """Преобразовать доменный отчёт в схему ответа."""

    payload = report.payload
    meta = ReportPayloadMetaOut(
        check_id=payload.meta.check_id,
        generated_at=payload.meta.generated_at,
        schema_version=payload.meta.schema_version,
        modules=list(payload.meta.modules),
        disclaimers=list(payload.meta.disclaimers),
    )
    payload_out = ReportPayloadOut(
        meta=meta,
        sections=payload.sections,
    )
    return ReportOut(
        report_id=report.id,
        check_id=report.check_id,
        status=report.status,
        created_at=report.created_at,
        modules=list(report.modules),
        payload=payload_out,
    )


def _module_error_detail(
    message: str,
    modules: list[str],
) -> dict[str, object]:
    """Сформировать payload ошибки модулей."""

    return {
        'message': message,
        'modules': modules,
    }
