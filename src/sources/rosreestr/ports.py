"""Порты клиентов Росреестра."""

from __future__ import annotations

from typing import Protocol

from sources.rosreestr.dto import RosreestrApiResponse


class RosreestrClientPort(Protocol):
    """Контракт клиента Росреестра."""

    def get_object(self, *, cadastral_number: str) -> RosreestrApiResponse:
        """Вернуть данные по кадастровому номеру."""

        raise NotImplementedError
