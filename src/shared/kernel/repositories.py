"""Провайдеры репозиториев с поддержкой in-memory и БД."""

from __future__ import annotations

from collections.abc import Callable
from typing import Any

from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker

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
from shared.kernel.settings import Settings, get_settings

SessionFactory = async_sessionmaker[AsyncSession]
_session_factory: SessionFactory | None = None


class _LazyRepo:
    """Ленивая обёртка над провайдером репозитория."""

    __slots__ = ('_factory', '_instance', '_context')

    def __init__(
        self,
        factory: Callable[[Settings, SessionFactory | None], Any],
    ) -> None:
        self._factory = factory
        self._instance: Any | None = None
        self._context: tuple[int, int] | None = None

    def reset(self) -> None:
        """Сбросить кэшированный экземпляр."""

        self._instance = None
        self._context = None

    def _resolve(self) -> Any:
        settings = get_settings()
        session_marker = id(_session_factory)
        context = (id(settings), session_marker)
        if self._instance is None or self._context != context:
            self._instance = self._factory(settings, _session_factory)
            self._context = context
        return self._instance

    def __getattr__(self, item: str) -> Any:
        return getattr(self._resolve(), item)


def configure_repositories(session_factory: SessionFactory) -> None:
    """Сохранить фабрику сессий для использования репозиториями."""

    global _session_factory
    _session_factory = session_factory
    check_results_repo.reset()
    check_cache_repo.reset()
    reports_repo.reset()


def _require_session_factory() -> SessionFactory:
    if _session_factory is None:
        raise RuntimeError('Session factory is not configured.')
    return _session_factory


def _build_check_results_repo(
    settings: Settings,
    session_factory: SessionFactory | None,
) -> Any:
    if settings.STORAGE_MODE == 'memory':
        return InMemoryCheckResultsRepo()

    return CheckResultsRepoDb(
        session_factory=session_factory or _require_session_factory(),
    )


def _build_check_cache_repo(
    settings: Settings,
    session_factory: SessionFactory | None,
) -> Any:
    if settings.STORAGE_MODE == 'memory':
        return InMemoryCheckCacheRepo(
            ttl_seconds=settings.CHECK_CACHE_TTL_SECONDS,
        )

    return CheckCacheRepoDb(
        session_factory=session_factory or _require_session_factory(),
        ttl_seconds=settings.CHECK_CACHE_TTL_SECONDS,
        cache_version=settings.CHECK_CACHE_VERSION,
    )


def _build_reports_repo(
    settings: Settings,
    session_factory: SessionFactory | None,
) -> Any:
    if settings.STORAGE_MODE == 'memory':
        return InMemoryReportsRepo()

    return ReportsRepoDb(
        session_factory=session_factory or _require_session_factory(),
    )


check_results_repo = _LazyRepo(_build_check_results_repo)
check_cache_repo = _LazyRepo(_build_check_cache_repo)
reports_repo = _LazyRepo(_build_reports_repo)
