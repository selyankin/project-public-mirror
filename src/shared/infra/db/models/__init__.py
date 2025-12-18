"""Регистрирует ORM-модели для Alembic."""

from shared.infra.db.models.check_cache import CheckCacheModel
from shared.infra.db.models.check_result import CheckResultModel
from shared.infra.db.models.report import ReportModel

__all__ = [
    'CheckCacheModel',
    'CheckResultModel',
    'ReportModel',
]
