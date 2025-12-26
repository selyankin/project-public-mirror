"""Исключения домена объявлений."""

from __future__ import annotations


class ListingError(Exception):
    """Базовая ошибка домена объявлений."""


class ListingNotSupportedError(ListingError):
    """Источник не умеет обрабатывать такой URL."""


class ListingFetchError(ListingError):
    """Ошибка при загрузке HTML объявления."""


class ListingParseError(ListingError):
    """Ошибка нормализации данных объявления."""
