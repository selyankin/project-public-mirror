"""Каталог доступных модулей отчёта."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Final


@dataclass(frozen=True, slots=True)
class ReportModuleSpec:
    """Описание отдельного модуля отчёта."""

    id: str
    title: str
    description: str
    is_paid: bool = False
    depends_on: tuple[str, ...] = ()


DEFAULT_MODULE_ID: Final[str] = 'base_summary'
DEFAULT_MODULES: Final[tuple[str, ...]] = (DEFAULT_MODULE_ID,)

DEFAULT_MODULE_SPECS: Final[list[ReportModuleSpec]] = [
    ReportModuleSpec(
        id='base_summary',
        title='Базовое резюме',
        description='Краткий обзор данных по проверке.',
        is_paid=False,
        depends_on=(),
    ),
    ReportModuleSpec(
        id='address_quality',
        title='Качество адреса',
        description='Подробный анализ нормализованного адреса.',
        is_paid=False,
        depends_on=(DEFAULT_MODULE_ID,),
    ),
    ReportModuleSpec(
        id='risk_signals',
        title='Сигналы риска',
        description='Список выявленных риск-сигналов.',
        is_paid=False,
        depends_on=(DEFAULT_MODULE_ID,),
    ),
    ReportModuleSpec(
        id='fias_normalization',
        title='FIAS нормализация',
        description='Расширенная нормализация через ФИАС.',
        is_paid=True,
        depends_on=(DEFAULT_MODULE_ID, 'address_quality'),
    ),
]

MODULE_CATALOG: Final[dict[str, ReportModuleSpec]] = {
    spec.id: spec for spec in DEFAULT_MODULE_SPECS
}
