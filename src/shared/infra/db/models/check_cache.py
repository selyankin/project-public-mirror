"""ORM-модель кэша результатов проверок."""

from __future__ import annotations

import uuid
from datetime import datetime

from sqlalchemy import DateTime, Index, Text, func
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column

from shared.kernel.db_base import Base


class CheckCacheModel(Base):
    """Представляет запись в кэше проверок."""

    __tablename__ = 'check_cache'
    __table_args__ = (Index('ix_check_cache_expires_at', 'expires_at'),)

    cache_key: Mapped[str] = mapped_column(
        Text,
        primary_key=True,
    )
    check_result_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        nullable=False,
    )
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        server_default=func.now(),
        nullable=False,
    )
    expires_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        nullable=False,
    )
    cache_version: Mapped[str] = mapped_column(
        Text,
        nullable=False,
        server_default='v1',
    )
