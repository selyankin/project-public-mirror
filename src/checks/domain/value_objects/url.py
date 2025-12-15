"""Value object для работы с исходными URL."""

from __future__ import annotations

from urllib.parse import urlparse


class UrlRaw:
    """Представление неподготовленного URL запроса."""

    __slots__ = ('value',)

    def __init__(self, value: str):
        """Создать объект сырых данных URL."""

        if not isinstance(value, str):
            raise ValueError('URL должен быть строкой.')

        trimmed = value.strip()
        if not trimmed:
            raise ValueError('URL не может быть пустым.')

        if len(trimmed) > 2000:
            raise ValueError('URL слишком длинный.')

        if not (
            trimmed.startswith('http://') or trimmed.startswith('https://')
        ):
            raise ValueError('URL должен начинаться с http:// или https://.')

        parsed = urlparse(trimmed)
        if parsed.scheme not in {'http', 'https'} or not parsed.netloc:
            raise ValueError('URL имеет недопустимый формат.')

        self.value = trimmed

    def __eq__(self, other: object) -> bool:
        """Сравнить URL по значению."""

        if not isinstance(other, UrlRaw):
            return NotImplemented

        return self.value == other.value

    def __hash__(self) -> int:
        """Вернуть хэш по значению URL."""

        return hash(self.value)
