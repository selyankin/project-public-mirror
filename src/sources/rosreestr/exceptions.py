"""Исключения интеграции с Росреестром."""

from __future__ import annotations


class RosreestrClientError(Exception):
    """Ошибка обращения к API Росреестра."""


class RosreestrResolveError(Exception):
    """Базовая ошибка use-case разрешения Росреестра."""


class RosreestrNotFoundError(RosreestrResolveError):
    """Объект Росреестра не найден."""


class RosreestrBadResponseError(RosreestrResolveError):
    """Некорректный ответ Росреестра."""
