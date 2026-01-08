"""Исключения GIS ЖКХ."""

from __future__ import annotations


class GisGkhError(Exception):
    """Базовая ошибка GIS ЖКХ."""


class GisGkhBadResponseError(GisGkhError):
    """Некорректный ответ GIS ЖКХ."""
