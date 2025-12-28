"""Singleton-контейнер для use-case Росреестра."""

from __future__ import annotations

from shared.kernel.rosreestr_client_factory import build_rosreestr_client
from shared.kernel.settings import Settings
from sources.rosreestr.use_cases.resolve_house_by_cadastral import (
    ResolveRosreestrHouseByCadastralUseCase,
)

_use_case: ResolveRosreestrHouseByCadastralUseCase | None = None


def get_rosreestr_resolver_use_case(
    settings: Settings,
) -> ResolveRosreestrHouseByCadastralUseCase:
    """Вернуть singleton use-case разрешения Росреестра."""

    global _use_case
    if _use_case is None:
        client = build_rosreestr_client(settings)
        _use_case = ResolveRosreestrHouseByCadastralUseCase(client=client)

    return _use_case


def reset_rosreestr_resolver_container() -> None:
    """Сбросить singleton (для тестов)."""

    global _use_case
    _use_case = None
