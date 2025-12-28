"""Контейнер use-case Росреестра."""

from __future__ import annotations

from shared.kernel.rosreestr_client_factory import build_rosreestr_client
from shared.kernel.settings import Settings
from sources.rosreestr.use_cases.resolve_house_by_cadastral import (
    ResolveRosreestrHouseByCadastralUseCase,
)

__all__ = ['build_resolve_house_use_case']


def build_resolve_house_use_case(
    settings: Settings,
) -> ResolveRosreestrHouseByCadastralUseCase:
    """Построить use-case разрешения по кадастровому номеру."""

    client = build_rosreestr_client(settings)
    return ResolveRosreestrHouseByCadastralUseCase(client=client)
