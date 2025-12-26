"""Проверки контейнера резолвинга листингов."""

from __future__ import annotations

import pytest

from checks.infrastructure.listing_resolver_container import (
    close_listing_resolver_container,
    get_listing_resolver_use_case,
)


@pytest.fixture(autouse=True)
def reset_container():
    """Очистить контейнер перед и после теста."""

    close_listing_resolver_container()
    yield
    close_listing_resolver_container()


def test_get_listing_resolver_returns_singleton() -> None:
    """Повторный вызов возвращает тот же объект."""

    first = get_listing_resolver_use_case()
    second = get_listing_resolver_use_case()
    assert first is second


def test_close_resets_singleton() -> None:
    """После закрытия создаётся новый use-case."""

    first = get_listing_resolver_use_case()
    close_listing_resolver_container()
    second = get_listing_resolver_use_case()
    assert first is not second
