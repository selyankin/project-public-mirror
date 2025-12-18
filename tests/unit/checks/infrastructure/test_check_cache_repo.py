"""Проверки in-memory кэша проверок."""

from datetime import UTC, datetime, timedelta
from uuid import uuid4

from checks.infrastructure.check_cache_repo_inmemory import (
    InMemoryCheckCacheRepo,
)


class DummyClock:
    """Управляемые часы для тестов."""

    def __init__(self) -> None:
        self.value = datetime(2024, 1, 1, tzinfo=UTC)

    def advance(self, seconds: int) -> None:
        """Сместить время вперёд."""

        self.value += timedelta(seconds=seconds)

    def __call__(self) -> datetime:
        """Вернуть текущее время."""

        return self.value


def test_cache_entry_expires_after_ttl() -> None:
    """Запись пропадает после истечения TTL."""

    clock = DummyClock()
    repo = InMemoryCheckCacheRepo(ttl_seconds=1, now_fn=clock)
    key = 'foo'
    check_id = uuid4()

    repo.set(key, check_id)
    assert repo.get(key) is not None

    clock.advance(2)
    assert repo.get(key) is None
