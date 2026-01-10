"""Исключения kad.arbitr.ru."""

from __future__ import annotations


class KadArbitrClientError(Exception):
    """Базовая ошибка клиента kad.arbitr.ru."""


class KadArbitrBlockedError(KadArbitrClientError):
    """Доступ к kad.arbitr.ru заблокирован или ограничен."""


class KadArbitrUnexpectedResponseError(KadArbitrClientError):
    """Неожиданный ответ от kad.arbitr.ru."""
