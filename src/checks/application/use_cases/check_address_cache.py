"""Вспомогательные функции кэша проверки."""

from __future__ import annotations

from uuid import UUID

from checks.application.ports.checks import (
    CheckCacheRepoPort,
    CheckResultsRepoPort,
)
from checks.domain.entities.check_result import CheckResultSnapshot
from checks.domain.helpers.idempotency import build_check_cache_key
from checks.domain.value_objects.query import CheckQuery


def build_cache_key(
    *,
    query: CheckQuery,
    cache_version: str,
    fias_mode: str,
) -> str:
    """Сформировать ключ кэша для запроса."""

    return build_check_cache_key(
        input_kind=query.type.value,
        input_value=query.query,
        fias_mode=fias_mode,
        version=cache_version,
    )


async def get_cached_snapshot(
    *,
    cache_repo: CheckCacheRepoPort,
    results_repo: CheckResultsRepoPort,
    key: str,
) -> tuple[CheckResultSnapshot | None, UUID | None]:
    """Вернуть снапшот проверки и идентификатор, если он есть."""

    entry = await cache_repo.get(key)
    if not entry:
        return None, None

    snapshot = await results_repo.get(entry.check_id)
    return snapshot, entry.check_id if snapshot else None
