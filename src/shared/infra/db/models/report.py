"""ORM-модель отчётов."""

from __future__ import annotations

import uuid
from datetime import datetime

from sqlalchemy import DateTime, Text, func
from sqlalchemy.dialects.postgresql import JSONB, UUID
from sqlalchemy.orm import Mapped, mapped_column

from shared.kernel.db_base import Base


class ReportModel(Base):
    """Представляет сгенерированный отчёт по проверке."""

    __tablename__ = 'reports'

    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        primary_key=True,
        default=uuid.uuid4,
    )
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        server_default=func.now(),
        nullable=False,
    )
    check_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        nullable=False,
    )
    status: Mapped[str] = mapped_column(Text, nullable=False)
    modules: Mapped[list[str]] = mapped_column(
        JSONB,
        nullable=False,
        default=list,
    )
    payload: Mapped[dict] = mapped_column(JSONB, nullable=False)
