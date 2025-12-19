"""Use-case создания отчёта по результату проверки адреса."""

from __future__ import annotations

from collections.abc import Sequence
from datetime import UTC, datetime
from typing import Any
from uuid import UUID, uuid4

from checks.application.ports.checks import CheckResultsRepoPort
from checks.domain.entities.check_result import CheckResultSnapshot
from reports.application.ports.repos import ReportsRepoPort
from reports.application.services.module_access_policy import (
    ModuleAccessPolicy,
)
from reports.application.services.module_builders import (
    DEFAULT_MODULE_BUILDERS,
)
from reports.application.services.payments_stub import PaymentsServiceStub
from reports.application.services.report_assembler import ReportAssembler
from reports.domain.entities.report import (
    Report,
    ReportPayload,
    ReportPayloadMeta,
)
from reports.domain.exceptions.report import CheckResultNotFoundError
from reports.domain.modules.validation import validate_modules

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
        '_assembler',
        '_module_access_policy',
    )

    def __init__(
        self,
        check_results_repo: CheckResultsRepoPort,
        reports_repo: ReportsRepoPort,
        payments_service: PaymentsServiceStub,
        report_assembler: ReportAssembler | None = None,
        module_access_policy: ModuleAccessPolicy | None = None,
    ) -> None:
        """Сохранить зависимости use-case."""

        self._check_results_repo = check_results_repo
        self._reports_repo = reports_repo
        self._payments_service = payments_service
        self._assembler = (
            report_assembler
            if report_assembler is not None
            else ReportAssembler(DEFAULT_MODULE_BUILDERS)
        )
        self._module_access_policy = (
            module_access_policy or ModuleAccessPolicy()
        )

    async def execute(self, check_id: UUID, modules: list[str]) -> Report:
        """Создать отчёт по сохранённому результату проверки."""

        snapshot = await self._check_results_repo.get(check_id)
        if snapshot is None:
            raise CheckResultNotFoundError(str(check_id))

        module_ids, _module_specs = validate_modules(
            modules,
            access_policy=self._module_access_policy,
        )
        self._payments_service.authorize(check_id, module_ids)

        created_at = datetime.now(UTC)
        check_payload = self._build_check_payload(snapshot, check_id)

        assembled = await self._assembler.assemble(check_payload, module_ids)
        assembled_meta = assembled['meta']
        assembled_meta['disclaimers'] = list(DEFAULT_DISCLAIMERS)

        payload = self._build_payload_entity(assembled, check_id)
        report = Report(
            id=uuid4(),
            check_id=check_id,
            created_at=created_at,
            status='ready',
            modules=list(module_ids),
            payload=payload,
        )

        await self._reports_repo.save(report)
        return report

    @staticmethod
    def _build_check_payload(
        snapshot: CheckResultSnapshot,
        check_id: UUID,
    ) -> dict[str, Any]:
        """Подготовить данные проверки для модулей отчёта."""

        normalized = snapshot.normalized_address
        return {
            'check_id': check_id,
            'kind': snapshot.kind,
            'raw_input': snapshot.raw_input,
            'normalized_address': {
                'raw': normalized.raw.value,
                'normalized': normalized.normalized,
                'confidence': normalized.confidence,
                'source': normalized.source,
                'tokens': list(normalized.tokens),
            },
            'risk_card': snapshot.risk_card.to_dict(),
            'signals': [signal.to_dict() for signal in snapshot.signals],
            'created_at': snapshot.created_at,
            'schema_version': snapshot.schema_version,
            'fias': snapshot.fias_payload,
        }

    @staticmethod
    def _build_payload_entity(
        assembled: dict[str, Any],
        check_id: UUID,
    ) -> ReportPayload:
        """Преобразовать собранный payload в доменную сущность."""

        meta_dict = dict(assembled.get('meta') or {})
        sections = dict(assembled.get('sections') or {})
        meta = ReportPayloadMeta(
            check_id=meta_dict.get('check_id', check_id),
            generated_at=meta_dict.get('generated_at', datetime.now(UTC)),
            schema_version=int(meta_dict.get('schema_version', 1)),
            modules=list(meta_dict.get('modules') or []),
            disclaimers=list(meta_dict.get('disclaimers') or []),
        )
        return ReportPayload(
            meta=meta,
            sections=sections,
        )
