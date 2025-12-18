"""Сущности, связанные с кэшем результатов проверки."""

from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime
from uuid import UUID


@dataclass(slots=True)
class CachedCheckEntry:
    """Описывает кэшированную запись проверки."""

    check_id: UUID
    created_at: datetime
    expires_at: datetime

    def is_expired(self, now: datetime) -> bool:
        """Проверить, протухла ли запись."""

        return now >= self.expires_at
