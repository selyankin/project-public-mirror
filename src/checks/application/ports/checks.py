"""Application ports for check-related services."""

from __future__ import annotations

from typing import Protocol
from uuid import UUID

from checks.domain.entities.check_cache import CachedCheckEntry
from checks.domain.entities.check_result import CheckResultSnapshot
from checks.domain.value_objects.address import (
    AddressNormalized,
    AddressRaw,
)
from risks.domain.entities.risk_card import RiskSignal


class AddressResolverPort(Protocol):
    """Порт сервиса нормализации адресов."""

    def normalize(self, raw: AddressRaw) -> AddressNormalized:
        """Преобразовать сырой адрес в каноничное представление."""


class SignalsProviderPort(Protocol):
    """Агрегирующий провайдер сигналов риска."""

    def collect(self, normalized: AddressNormalized) -> tuple[RiskSignal, ...]:
        """Собрать агрегированный набор сигналов по адресу."""


class CheckResultsRepoPort(Protocol):
    """Порт для сохранения и чтения результатов проверок."""

    async def save(self, result: CheckResultSnapshot) -> UUID:
        """Сохранить результат и вернуть идентификатор."""

    async def get(self, check_id: UUID) -> CheckResultSnapshot | None:
        """Получить сохранённый результат."""


class CheckCacheRepoPort(Protocol):
    """Порт кэша результатов проверок."""

    async def get(self, key: str) -> CachedCheckEntry | None:
        """Вернуть кэшированную запись."""

    async def set(self, key: str, check_id: UUID) -> None:
        """Сохранить запись для указанного ключа."""

    async def cleanup(self) -> None:
        """Удалить протухшие записи."""
