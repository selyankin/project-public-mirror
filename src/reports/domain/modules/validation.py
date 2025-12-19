"""Валидация списка модулей отчёта."""

from __future__ import annotations

from collections.abc import Iterable

from reports.application.services.module_access_policy import (
    ModuleAccessPolicy,
)
from reports.domain.exceptions.report import (
    ReportInvalidModulesError,
    ReportModuleNotFoundError,
)
from reports.domain.modules.catalog import (
    DEFAULT_MODULES,
    MODULE_CATALOG,
    ReportModuleSpec,
)


def validate_modules(
    requested: Iterable[str] | None,
    *,
    access_policy: ModuleAccessPolicy | None = None,
) -> tuple[list[str], list[ReportModuleSpec]]:
    """Проверить список модулей, вернуть ids и спецификации."""

    if requested is None:
        module_ids = list(DEFAULT_MODULES)
    else:
        module_ids = list(requested)
        if not module_ids:
            raise ReportInvalidModulesError(
                'modules list must not be empty',
                [],
            )
    validated: list[str] = []
    specs: list[ReportModuleSpec] = []
    seen: set[str] = set()

    def _add(m_id: str) -> None:
        if m_id in seen:
            return

        spec = MODULE_CATALOG.get(m_id)
        if spec is None:
            raise ReportModuleNotFoundError(m_id)

        for dependency in spec.depends_on:
            _add(dependency)

        seen.add(m_id)
        validated.append(m_id)
        specs.append(spec)

    for module_id in module_ids:
        _add(module_id)

    policy = access_policy or ModuleAccessPolicy()
    policy.ensure_access(specs)
    return validated, specs
