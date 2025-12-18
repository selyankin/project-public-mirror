"""Заглушка платёжного сервиса."""

from __future__ import annotations

from collections.abc import Sequence
from uuid import UUID


class PaymentsServiceStub:
    """Имитация авторизации платежа за отчёт."""

    __slots__ = ()

    def authorize(self, check_id: UUID, modules: Sequence[str]) -> None:
        """Подтвердить оплату (всегда успех)."""

        _ = (check_id, modules)
        return
