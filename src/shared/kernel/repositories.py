"""Провайдеры репозиториев с поддержкой in-memory и БД."""

from __future__ import annotations

from collections.abc import Callable
from typing import Any

from checks.infrastructure.check_cache_repo_db import CheckCacheRepoDb
from checks.infrastructure.check_cache_repo_inmemory import (
    InMemoryCheckCacheRepo,
)
from checks.infrastructure.check_results_repo_db import CheckResultsRepoDb
from checks.infrastructure.check_results_repo_inmemory import (
    InMemoryCheckResultsRepo,
)
from reports.infrastructure.reports_repo_db import ReportsRepoDb
from reports.infrastructure.reports_repo_inmemory import (
    InMemoryReportsRepo,
)
from shared.kernel.db import get_session_factory
from shared.kernel.settings import Settings, get_settings


class _LazyRepo:
    """Ленивый обёртка над провайдером репозитория."""

    __slots__ = ('_factory', '_instance', '_settings_id')

    def __init__(self, factory: Callable[[Settings], Any]) -> None:
        self._factory = factory
        self._instance: Any | None = None
        self._settings_id: int | None = None

    def _resolve(self) -> Any:
        settings = get_settings()
        settings_id = id(settings)
        if self._instance is None or self._settings_id != settings_id:
            self._instance = self._factory(settings)
            self._settings_id = settings_id
        return self._instance

    def __getattr__(self, item: str) -> Any:
        return getattr(self._resolve(), item)


def _build_check_results_repo(settings: Settings) -> Any:
    if settings.STORAGE_MODE == 'memory':
        return InMemoryCheckResultsRepo()

    return CheckResultsRepoDb(session_factory=get_session_factory())


def _build_check_cache_repo(settings: Settings) -> Any:
    if settings.STORAGE_MODE == 'memory':
        return InMemoryCheckCacheRepo(
            ttl_seconds=settings.CHECK_CACHE_TTL_SECONDS,
        )

    return CheckCacheRepoDb(
        session_factory=get_session_factory(),
        ttl_seconds=settings.CHECK_CACHE_TTL_SECONDS,
        cache_version=settings.CHECK_CACHE_VERSION,
    )


def _build_reports_repo(settings: Settings) -> Any:
    if settings.STORAGE_MODE == 'memory':
        return InMemoryReportsRepo()

    return ReportsRepoDb(session_factory=get_session_factory())


check_results_repo = _LazyRepo(_build_check_results_repo)
check_cache_repo = _LazyRepo(_build_check_cache_repo)
reports_repo = _LazyRepo(_build_reports_repo)
