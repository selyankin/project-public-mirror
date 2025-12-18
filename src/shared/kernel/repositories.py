"""In-memory singletons для временных хранилищ."""

from checks.infrastructure.check_cache_repo_inmemory import (
    InMemoryCheckCacheRepo,
)
from checks.infrastructure.check_results_repo_inmemory import (
    InMemoryCheckResultsRepo,
)
from reports.infrastructure.reports_repo_inmemory import InMemoryReportsRepo
from shared.kernel.settings import get_settings


class _LazyCheckCacheRepo:
    """Ленивая инициализация кэша с зависимостью от настроек."""

    __slots__ = ('_repo',)

    def __init__(self) -> None:
        self._repo: InMemoryCheckCacheRepo | None = None

    def _ensure(self) -> InMemoryCheckCacheRepo:
        if self._repo is None:
            settings = get_settings()
            self._repo = InMemoryCheckCacheRepo(
                ttl_seconds=settings.CHECK_CACHE_TTL_SECONDS,
            )

        return self._repo

    def __getattr__(self, item):
        return getattr(self._ensure(), item)


check_results_repo = InMemoryCheckResultsRepo()
check_cache_repo = _LazyCheckCacheRepo()
reports_repo = InMemoryReportsRepo()
