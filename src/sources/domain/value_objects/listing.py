"""Value-объекты объявлений."""

from __future__ import annotations

from dataclasses import dataclass
from urllib.parse import urlparse


@dataclass(frozen=True, slots=True)
class ListingUrl:
    """URL объявления с базовой валидацией схемы и хоста."""

    value: str

    def __post_init__(self) -> None:
        """Проверить, что URL корректен и использует http/https."""

        parsed = urlparse(self.value or '')
        if parsed.scheme.lower() not in {'http', 'https'}:
            raise ValueError('URL должен начинаться с http(s)')

        if not parsed.netloc:
            raise ValueError('URL должен содержать хост')

    def __str__(self) -> str:
        """Вернуть строковое представление."""

        return self.value


@dataclass(frozen=True, slots=True)
class ListingId:
    """Идентификатор объявления."""

    value: str

    def __post_init__(self) -> None:
        """Проверить, что идентификатор не пустой и без пробелов."""

        if not isinstance(self.value, str):
            raise ValueError('ListingId должен быть строкой')

        stripped = self.value.strip()
        if not stripped:
            raise ValueError('ListingId не может быть пустым')

        if any(ch.isspace() for ch in stripped):
            raise ValueError('ListingId не должен содержать пробелы')

    def __str__(self) -> str:
        """Вернуть текстовое значение."""

        return self.value
